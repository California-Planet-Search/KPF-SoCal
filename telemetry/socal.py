############################################################
#
#  socal.py
#
#  Object-oriented SoCal module containing 
#  wrappers for commands/routines 
#
#  Author: Ryan Rubenzahl
#  Last edit: 2/2/2022
#
############################################################

import socket
import eko_commands as eko 

# Global static variables
TCP_IP   = '192.168.23.232' # Lantronix IP address
TCP_PORT = 10001 # Local Port for Serial 1 (EKO Tracker) on Lantronix
BUFFER_SIZE = 80 # Max number of bytes to read out

class SoCal(object):

    def __init__(self):
        '''
        Initialize SoCal object and open 
        the connection to the TCP/IP port
        '''
        self.tracker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.BUFFER_SIZE = BUFFER_SIZE

        # Open connection to TCP/IP port 
        self.tracker.connect((TCP_IP, TCP_PORT))
        print('Connected to {} at Port {}'.format(*self.tracker.getpeername()))
        
    def set_datetime(self, date, time):
        command = eko.set_datetime(date, time)
        return eko.send_command(command, self.tracker)

    def set_location(self, lat, lon):
        command = eko.set_location(lat, lon)
        return eko.send_command(command, self.tracker)

    def set_tracking_mode(self, mode):
        command = eko.set_tracking_mode(mode)
        return eko.send_command(command, self.tracker)

    def set_position(self, alt, az):
        command = eko.set_position(alt, az)
        return eko.send_command(command, self.tracker)
    
    def get_datetime(self):
        return eko.get_datetime(self.tracker)

    def get_location(self):
        return eko.get_location(self.tracker)

    def get_tracking_mode(self):
        return eko.get_tracking_mode(self.tracker)

    def get_corrected_position(self):
        return eko.get_corrected_position(self.tracker)
    
    def get_calculated_position(self):
        return eko.get_calculated_position(self.tracker)
   
    def get_sun_sensor_offset(self):
        return eko.get_sun_sensor_offset(self.tracker)
    
    def get_firmware_version(self):
        return eko.get_firmware_version(self.tracker)

    def slew(self, alt, az, new_mode='0'):
        '''
        Switches to manual pointing and slews the tracker to the desired position 
        
        Args:
            alt: (float) altitude in decimal degrees to slew to (e.g. 15.123)
            az:  (float) azimuth in decimal degrees to slew to (e.g. 123.133)
            new_mode: After slewing, remain in manual pointing mode [default]
                                or switch to tracking mode '1', '2', or '3'
        Returns:
            alt: (float) tracker altitude in decimal degrees (e.g. 15.123)
            az:  (float) tracker azimuth in decimal degrees (e.g. 123.133)
        '''
        print('Slewing to\n\tAlt = {:.3f}\n\t Az = {:.3f}'.format(alt, az))

        # 1. Set the tracker to Manual command mode (if not already)
        if not self.get_tracking_mode() == '0':
            response = self.set_tracking_mode('0')
            if response is None or len(response) == 0 or response == 'ERR':
                print('BAD OUTPUT:', response)
                return
            else:
                print(response)

        # 2. Slew to desired alt/az
        response = self.set_position(alt, az)
        if response is None:
            print('SLEW ERROR:', response)
            return
        else:
            print(response)

        # 3. Read the current pointing position
        response = self.get_corrected_position()
        if response is None:
            print('ERROR:', response)
            return
        else:
           alt, az = response
           print('Now pointing at\n\tAlt = {:.3f}\n\t Az = {:.3f}'.format(alt, az))

        # 4. Set new tracking mode 
        if new_mode == '0':
            return
        else:
            assert new_mode in ['1', '2', '3'], 'Invalid tracking mode {}, must be 1, 2, or 3'.format(new_mode)
            response = self.set_tracking_mode(new_mode)
            if response is None:
                return
            else:
                print(response)

    def initialize(ser):
        '''
        Initialize the SoCal after powering on

        Args:
            ser: pyserial object of the serial port to send the command to

        Returns:
            status: status of tracker after startup
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
        status = 'Date/Location/other info we care about'
        status += 'Pointing mode: '
        return status
