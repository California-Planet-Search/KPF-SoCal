############################################################
#
#  socal.py
#
#  Object-oriented SoCal module containing 
#  wrappers for commands/routines 
#
#  Author: Ryan Rubenzahl
#  Last edit: 3/26/2021
#
############################################################

import serial
import .commands as cmd 
import .eko_commands as eko 

class SoCal(object):

    def __init__(self, port='COM3'):
        '''
        Initialize SoCal object and open serial port
        '''
        self.ser = serial.Serial(port)
        
    def set_datetime(self, date, time):
        command = eko.set_datetime(date, time)
        eko.send_command(command, self.ser)

    def set_location(self, lat, lon):
        command = eko.set_location(lat, lon)
        eko.send_command(command, self.ser)

    def set_tracking_mode(self, mode):
        command = eko.set_tracking_mode(mode)
        eko.send_command(command, self.ser)

    def set_position(self, alt, az):
        command = eko.set_position(alt, az)
        eko.send_command(command, self.ser)
    
    def get_datetime(self):
        return eko.get_datetime(self.ser)

    def get_location(self):
        return eko.get_location(self.ser)

    def get_tracking_mode(self):
        return eko.get_tracking_mode(self.ser)

    def get_corrected_position(self):
        return eko.get_corrected_position(self.ser)
    
    def get_calculated_position(self):
        return eko.get_calculated_position(self.ser)
   
    def get_sun_sensor_offset(self):
        return eko.get_sun_sensor_offset(self.ser)
    
    def get_firmware_version(self):
        return eko.get_firmware_version(self.ser)

    def slew(ser, alt, az, keep_manual=True):
        '''
        Switches to manual pointing and slews the tracker to the desired position 
        
        Args:
            ser: pyserial object of the serial port to send the command to
            alt: (float) altitude in decimal degrees to slew to (e.g. 15.123)
            az:  (float) azimuth in decimal degrees to slew to (e.g. 123.133)
            keep_manual (bool): After slewing, remain in manual pointing mode 
                                or revert to autonomous tracking?
        Returns:
            alt: (float) tracker altitude in decimal degrees (e.g. 15.123)
            az:  (float) tracker azimuth in decimal degrees (e.g. 123.133)
        '''
        print('Slewing to\n\tAlt = {:.3f}\n\tAz = {:.3f}'.format(alt, az))

        # 1. Set the tracker to Manual command mode
        cmd = set_tracking_mode('0')
        output = send_command(cmd, ser)
        if output is None:
            # TODO: Shouldn't this be a check on if output='ERR'
            return
        else:
            print(output)

        # 2. Slew to desired alt/az
        cmd = set_position(alt, az)
        output = send_command(cmd, ser)
        if output is None:
            return
        else:
            print(output)

        # TODO: How to check if slewing/when done slewing?

        # 3. Read the current pointing position
        #output = get_corrected_position(ser)
        #if output is None:
        #    return
        #else:
        #   alt, az = output
        #   print('Now pointing at\n\tAlt = {:.3f}\n\tAz = {:.3f}'.format(alt, az))

        if keep_manual:
            return
        else:
            cmd = set_tracking_mode('3')
            output = send_command(cmd, ser)
            if output is None:
                return
            else:
                print(output)

    def initialize(ser):
        '''
        Initialize the SoCal after powering on

        Args:
            ser: pyserial object of the serial port to send the command to

        Returns:
            output: status of tracker after startup
        '''

        # TODO
        # Get current tracking mode
        # Confirm auto tracking mode
        # If not, set to auto

        # Confirm date/time is correct
        # Confirm lat/lon is correct

        # Confirm pointing at sun
            # Get current pointing angle
            # Estimate sun position and convert to alt/az

        # Confirm active tracking

        # Record test observation

        return
