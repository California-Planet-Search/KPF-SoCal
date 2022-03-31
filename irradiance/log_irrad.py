import sys
import csv
import time
from astropy.time import Time
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.exceptions import ModbusIOException

TCP_IP = '192.168.23.243' # Lantronix UDS1100-IAP 
TCP_PORT = 502 # Standard/default port for Modbus

# Open connection to Lantronix UDS1100-IAP
client = ModbusTcpClient(host=TCP_IP, port=TCP_PORT,
                         baudrate=9600, # 9600
                         timeout=3,  # default is 3 sec
                         parity='N', # none/odd/even
                         stopbits=2, # 2 if parity=none, 1 if parity=odd/even,
                         bytesize=8, # data length is 8 bits
                        )

try:
    with open(sys.argv[1], 'a') as f:
        writer = csv.writer(f)#, delimiter=',', lineterminator='\n')
        if client.connect():
            print('Connected to {} at port {}.'.format(TCP_IP, TCP_PORT))
            print('Logging irradiance data...')
            while True:
                
                # Min and Max Irradiance settings on registers 13, 14 (UINT16)
                rr = client.read_holding_registers(address=13, count=2, unit=1)
                if type(rr) is ModbusIOException:
                    continue
                else:
                    min_irrad, max_irrad = rr.registers

                jd = Time.now().jd
                # Read all at once to save time
                rr = client.read_holding_registers(address=16, count=9, unit=1)
                if type(rr) is ModbusIOException:
                    continue
                else:
                    # Get register values
                    r  = rr.registers

                    # Pyranometer Sensitivity on registers 16, 17 (FLOAT)
                    decoder = BinaryPayloadDecoder.fromRegisters(r[0:2], Endian.Big, wordorder=Endian.Little)
                    sens = decoder.decode_32bit_float()

                    # Input voltage (aka raw output from pyrheliometer, FLOAT) on 19, 20
                    decoder = BinaryPayloadDecoder.fromRegisters(r[3:5], Endian.Big, wordorder=Endian.Little)
                    voltage = decoder.decode_32bit_float()

                    # Solar Irradiance on registers 21, 22 (FLOAT)
                    decoder = BinaryPayloadDecoder.fromRegisters(r[5:7], Endian.Big, wordorder=Endian.Little)
                    solar_irrad = decoder.decode_32bit_float() 

                    # Pyrheliometer temperature o registers 23, 24 (FLOAT)
                    decoder = BinaryPayloadDecoder.fromRegisters(r[7:9], Endian.Big, wordorder=Endian.Little)
                    temp = decoder.decode_32bit_float()    

                # Write to file
                writer.writerow([jd, min_irrad, max_irrad, sens, voltage, solar_irrad, temp])
                time.sleep(1)

except KeyboardInterrupt:
    print('Closing connection.')
    client.close()
