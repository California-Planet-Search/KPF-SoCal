############################################################
#
#  pyrheliometer.py
#
#  Objects/functions for reading data from the EKO MS-57
#  through the MC-20 modbus signal converter
#
#  Author: Ryan Rubenzahl
#
############################################################

import numpy as np
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.exceptions import ModbusIOException

# Global static variables
TCP_IP   = '192.168.23.243' # Lantronix UDS1100-IAP IP address
TCP_PORT = 502 # Standard/default port for Modbus

class EKOPyrheliometer(object):

    def __init__(self):
        '''
        Initialize pyrheliometer object and open 
        the connection to the TCP/IP port
        '''
        self.client = ModbusTcpClient(host=TCP_IP, port=TCP_PORT,
                                      baudrate=9600, # 9600
                                      timeout=3,  # default is 3 sec
                                      parity='N', # N/O/E = none/odd/even
                                      stopbits=2, # 2 if parity=none, 1 if parity=odd/even,
                                      bytesize=8, # data length is 8 bits
                                      )
        print('Connected to {} at Port {}'.format(TCP_IP, TCP_PORT))

    def close_connection(self):
        '''
        Close the Modbus TCP client
        '''
        self.client.close()
        print('Closed connection to {} at Port {}'.format(TCP_IP, TCP_PORT))

    def poll(self):
        '''
        Poll values from the MS-57 pyrheliometer

        Returns:
              time_poll : [JD] Timestamp of the poll
              min_irrad : [W/m^2] Minimum irradiance value the MC-20 signal converter will output
              max_irrad : [W/m^2] Maximum irradiance value the MC-20 signal converter will output
            sensitivity : [uV/W/m^2] Sensitivity of the MC-20 signal converter
            out_voltage : [mV] Output voltage of the MS-57 as recorded by the MC-20 in millivolts
            solar_irrad : [W/m^2] Direct normal irradiance = 1e3*out_voltage/sensitivity
            temperature : [deg C] MS-57 temperature (heater)
        '''

        # Minimum and Maximum Irradiance settings on registers 13, 14 (UINT16)
        rr = self.client.read_holding_registers(address=13, count=2, unit=1)
        if type(rr) is ModbusIOException:
            print('ModbusIOException when polling min/max irradiance')
            min_irrad, max_irrad = np.nan, np.nan
        else:
            min_irrad, max_irrad = rr.registers
            
        # Remaining parameters are all floats so we can read them all at once
        rr = self.client.read_holding_registers(address=16, count=9, unit=1)
        if type(rr) is ModbusIOException:
            sensitivity, out_voltage, solar_irrad, temperature = np.nan, np.nan, np.nan, np.nan
        else:
            # Get register values
            r  = rr.registers

            # Pyranometer Sensitivity on registers 16, 17 (FLOAT)
            decoder = BinaryPayloadDecoder.fromRegisters(r[0:2], Endian.Big, wordorder=Endian.Little)
            sensitivity = decoder.decode_32bit_float()

            # Input voltage (aka raw output from pyrheliometer, FLOAT) on 19, 20
            decoder = BinaryPayloadDecoder.fromRegisters(r[3:5], Endian.Big, wordorder=Endian.Little)
            out_voltage = decoder.decode_32bit_float()

            # Solar Irradiance on registers 21, 22 (FLOAT)
            decoder = BinaryPayloadDecoder.fromRegisters(r[5:7], Endian.Big, wordorder=Endian.Little)
            solar_irrad = decoder.decode_32bit_float() 

            # Pyrheliometer temperature o registers 23, 24 (FLOAT)
            decoder = BinaryPayloadDecoder.fromRegisters(r[7:9], Endian.Big, wordorder=Endian.Little)
            temperature = decoder.decode_32bit_float()    

        return min_irrad, max_irrad, sensitivity, out_voltage, solar_irrad, temperature