############################################################
#
#  socal.py
#
#  Object-oriented SoCal module containing 
#  wrappers for commands/routines 
#
#  Author: Ryan Rubenzahl
#  Last edit: 3/31/2022
#
############################################################

import socket
import eko_commands as eko 

# Global static variables
TCP_IP   = '192.168.23.242' # Lantronix UDS2100 IP address
TCP_PORT = 10001 # Local port for serial 1 on UDS2100 

class SoCal(object):

    def __init__(self):
        '''
        Initialize SoCal object and open 
        the connection to the TCP/IP port
        '''
        self.tracker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tracker.connect((TCP_IP, TCP_PORT))
        print('Connected to {} at Port {}'.format(*self.tracker.getpeername()))
        
    def set_datetime(self, date, time):
        '''
        Set date and time (UTC)

        Args:
            date: (string) date in YYYY-MM-DD format (e.g. '2020-09-16')
            time: (string) time in hh:mm:ss format   (e.g. '12:34:56')

        Returns:
            Response from tracker.
        '''
        command = eko.set_datetime(date, time)
        return eko.send_command(command, self.tracker, wait_for_response=True)

    def set_location(self, lat, lon):
        '''
        Manually set the latitude and longitude of the tracker.
        This should be obtained automatically by the onboard GPS.
 
        Args:
            lat: (float) latitude in decimal degrees, + North, - South (e.g. 35.67199)
            lon: (float) longitude in decimal degrees, + East, - West (e.g. 139.67500)

        Returns:
            Response from tracker.
        '''
        command = eko.set_location(lat, lon)
        return eko.send_command(command, self.tracker, wait_for_response=True)

    def set_tracking_mode(self, mode):
        '''
        Set tracking mode. Use '3' for normal operation.
        Tracking angle includes the pointing error obtained from the sun-sensor.

        Args:
            mode: (str) tracking mode code
                '0': Manual tracking mode
                '1': Calculation tracking mode
                '2': Sun-sensor tracking mode
                '3': Sun-sensor with learning tracking mode

        Returns:
            Response from tracker.
        '''
        command = eko.set_tracking_mode(mode)
        return eko.send_command(command, self.tracker, wait_for_response=True)

    def set_position(self, alt, az):
        '''
        Set the tracker position (must be in manual pointing).

        Args:
            alt: (float) altitude in decimal degrees (0 = Horizon, 90 = Zenith)
            az:  (float) azimuth in decimal degrees  (0 = South, 180 = North)

        Returns:
            Response from tracker.
        '''
        command = eko.set_position(alt, az)
        return eko.send_command(command, self.tracker, wait_for_response=True)
    
    def get_datetime(self):
        '''
        Get date and time (UTC)

        Returns:
            datetime: datetime string formatted as YYYY-MM-DDThh:mm:ss
        '''
        return eko.get_datetime(self.tracker)

    def get_location(self):
        '''
        Get the latitude and longitude of the tracker

        Returns:
            lat: (float) latitude in decimal degrees, + North, - South (e.g. 35.67199)
            lon: (float) longitude in decimal degrees, + East, - West (e.g. 139.67500)
        '''
        return eko.get_location(self.tracker)

    def get_tracking_mode(self):
        '''
        Get the active tracking mode.

        Returns:
            mode: (str) tracking mode code
                '0': Manual tracking mode
                '1': Calculation tracking mode
                '2': Sun-sensor tracking mode
                '3': Sun-sensor with learning tracking mode
        '''
        return eko.get_tracking_mode(self.tracker)

    def get_corrected_position(self):
        '''
        Get the current tracker position.
        Equal to get_calculated_position() + get_sun_sensor_offset() 

        Returns:
            alt: (float) altitude in decimal degrees, + Upper, - Lower (e.g. 15.123)
            az:  (float) azimuth in decimal degrees, + West, - East, (e.g. 123.133)
        '''
        return eko.get_corrected_position(self.tracker)
    
    def get_calculated_position(self):
        '''
        Get the calculated solar position, i.e. prediction
        based on latitude/longitude/date/time (from GPS).

        Returns:
            alt: (float) altitude in decimal degrees, + Upper, - Lower (e.g. 15.123)
            az:  (float) azimuth in decimal degrees, + West, - East, (e.g. 123.133)
        '''
        return eko.get_calculated_position(self.tracker)
   
    def get_sun_sensor_offset(self):
        '''
        Get the offset angle from the sun sensor (test only) between
        the calculated solar position and the actual solar position.

        Returns:
            ha: (float) horizontal angle in decimal degrees
            va: (float) vertical angle in decimal degrees
        '''
        return eko.get_sun_sensor_offset(self.tracker)
    
    def get_firmware_version(self):
        '''
        Get the tracker firmware version

        Returns:
            v: (str) firmware version (latest version as of May 15, 2003 is 3.00)
        '''
        return eko.get_firmware_version(self.tracker)


    def slew(self, alt, az, new_mode='0'):
        '''
        Switches to manual pointing mode and 
        slews the tracker to the desired position 
        
        Args:
            alt: (float) altitude in decimal degrees to slew to (e.g. 15.123)
            az:  (float) azimuth in decimal degrees to slew to (e.g. 123.133)
            new_mode: After slewing, remain in manual pointing mode [default]
                                or switch to tracking mode `new_mode`
        Returns:
            alt: (float) tracker altitude in decimal degrees (e.g. 15.123)
            az:  (float) tracker azimuth in decimal degrees (e.g. 123.133)
        '''

        # 1. Set the tracker to Manual command mode (if not already)
        if not (self.get_tracking_mode() == '0'):
            response = self.set_tracking_mode('0')
            if response is None or len(response) == 0 or response == 'ERR':
                print('BAD OUTPUT:', response)
                return
            else:
                print(response)

        # 2. Slew to desired alt/az
        print('Slewing to\n\tAlt = {:.3f}\n\t Az = {:.3f}'.format(alt, az))
        response = self.set_position(alt, az)
        if response is None:
            print('No response from tracker after slewing.')
            return
        else:
            print(response)

        # 3. Read the current pointing position
        response = self.get_corrected_position()
        if response is None:
            print('No response from tracker.')
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
                print('ERROR:', response)
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
