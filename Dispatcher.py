############################################################
# 
#  Dispatcher.py
#
#  KTL dispatcher for SoCal
#  Wraps the dome && tracker objects in dome.py and sun_tracker.py
#
#  Author: Ryan Rubenzahl
#  Last edit: 8/25/2022
#
############################################################

import time
from control import dome, sun_tracker

dispatcher = None

def CreateDispatcher():
    global dispatcher
    # try:
    dispatcher = SoCalDispatcher()
    # dispatcher = 'TESTTEST'
    print('Connected to SoCalDispatcher.')
    # except:
    #     print('Could not create SoCalDispatcher.')

def connect():
    if  dispatcher is None:
        print('SoCalDispatcher is not active.')
        # TODO: change to exception?
    else:
        print('Connected to SoCalDispatcher.')
    return dispatcher

class SoCalDispatcher(object):

    def __init__(self):

        # Try to open a connection to the Dome
        try:
            self.dome = dome.DougDimmadome()
        except:
            print('Unable to connect to DomeGuard at {}/{}'.format(dome.DOME_IP, dome.DOME_PORT))

        # Try to open a connection to the tracker
        try:
            self.tracker = sun_tracker.EKOSunTracker()
        except:
            print('Unable to connect to EKO Sun Tracker at {}/'.format(sun_tracker.TCP_IP, sun_tracker.TCP_PORT))
        
        # High-level keywords 
        self._is_guiding = False
        self._slew = False
        self._alt_to_slew = None
        self._az_to_slew  = None
        self._domeopen = False
        self._domeclosed = True

    ############ EKO Sun Tracker Keywords ############
    @property
    def is_guiding(self):
        return self._is_guiding

    @is_guiding.setter
    def is_guiding(self, new_is_guiding):
        '''
        Set the tracker to be actively guiding or not (manual pointing mode)
        '''
        if new_is_guiding and not self.is_guiding:
            self.slew(True)
            self.tracking_mode('3')
            self.slew(False) # TODO: how to do check to confirm tracker is done moving
        elif not new_is_guiding and self.is_guiding:
            self.tracking_mode('0')
        else:
            return
        self._is_guiding = new_is_guiding

    @property
    def tracking_mode(self):
        return self.tracker.get_tracking_mode()

    @tracking_mode.setter
    def tracking_mode(self, mode):
        '''
        Set the Sun tracker tracking mode
        Valid tracking modes:
            '0': Manual tracking mode
            '1': Calculation tracking mode
            '2': Sun-sensor tracking mode
            '3': Sun-sensor with learning tracking mode (default for normal use)
        '''
        assert str(mode) in ['0', '1', '2', '3']
        self.tracker.set_tracking_mode(str(mode))

    @property
    def slew(self):
        return self._slew

    @slew.setter
    def slew(self, slew_tracker):
        '''
        Slew the tracker, if `alt_to_slew` and `az_to_slew` are both set
        '''
        assert not self.slew, 'Please wait until current slew is complete before sending a new slew command.'
        assert slew_tracker, 'Keyword `slew` is already False.'
        self._slew = True
        if (not self.az_to_slew is None) and (not self.alt_to_slew is None):
            self.tracker.slew(self.alt_to_slew, self.az_to_slew)
        else:
            print('CANNOT SLEW: Must set both\nalt_to_slew: {}\naz_to_slew: {}'.format(self.alt_to_slew, self.az_to_slew))
        # Reset slew staging
        self._slew = False
        self.alt_to_slew(None)
        self.az_to_slew(None)

    @property
    def alt_to_slew(self):
        return self._alt_to_slew

    @alt_to_slew.setter
    def alt_to_slew(self, alt):
        '''
        Set the altitude to move the tracker to
        Will not slew until both `alt_to_slew` and `az_to_slew` 
        are  both set followed by a call to `set slew True`

        Args:
            alt: (float) altitude in decimal degrees (0 = Horizon, 90 = Zenith)
        '''
        assert (alt >= 0) and (alt <90), 'ALT: {} is out of range [0, 90)'.format(alt)
        self._alt_to_slew = alt

    @property
    def az_to_slew(self):
        return self._az_to_slew
    
    @az_to_slew.setter
    def az_to_slewO(self, az):
        '''
        Set the azimuth to move the tracker to.
        Will not slew until both `alt_to_slew` and `az_to_slew` 
        are  both set followed by a call to `set slew True`

        Args:
            az:  (float) azimuth in decimal degrees  (0 = South, 180 = North, +90 = East, -90 = West) TODO: verif E/W
        '''
        assert (az >= -180) and (az <=180), 'AZ: {} is out of range (-180, 180)'.format(alt)
        self._az_to_slew = az

    @property
    def current_alt(self):
        '''
        Request the current pointing altitude from the Sun tracker
        '''
        alt, az = self.tracker.get_corrected_position()
        return alt

    @property
    def current_az(self):
        '''
        Request the current pointing azimuth from the Sun tracker
        '''
        alt, az = self.tracker.get_corrected_position()
        return az

    @property
    def pred_sun_alt(self):
        '''
        Request the calculated current altitude of the Sun from the Sun tracker
        '''
        alt, az = self.tracker.get_calculated_position()
        return alt
        
    @property
    def pred_sun_az(self):
        '''
        Request the calculated current altitude of the Sun from the Sun Tracker
        '''
        alt, az = self.tracker.get_calculated_position()
        return az

    @property
    def guiding_offset_alt(self):
        '''
        Request the altitude offset of the Sun measured by the sun sensor
        on the Sun Tracker. This is the equal to the difference between 
        `current_alt` and `pred_sun_alt`
        '''
        az_offset, alt_offset = self.tracker.get_sun_sensor_offset()
        return alt_offset

    @property
    def guiding_offset_az(self):
        '''
        Request the azimuth offset of the Sun measured by the sun sensor
        on the Sun Tracker. This is the equal to the difference between 
        `current_az` and `pred_sun_az`
        '''
        az_offset, alt_offset = self.tracker.get_sun_sensor_offset()
        return az_offset

    @property
    def datetime(self):
        '''
        Request the current date and time from the Sun Tracker's GPS
        '''
        return self.tracker.get_datetime()

    @property
    def location_latitude(self):
        '''
        Request the Sun Tracker's latitude from the onboard GPS
        '''
        lat, lon = self.tracker.get_location()
        return lat

    @property
    def location_longitude(self):
        '''
        Request the Sun Tracker's longitude from the onboard GPS
        '''
        lat, lon = self.tracker.get_location()
        return lon

    @property
    def sun_tracker_firmware(self):
        '''
        Request the Sun Tracker's current firmware version
        '''
        return self.tracker.get_firmware_version()
   
    # @property
    def on_sun(self, THRESHOLD=0.1):
        '''
        Determine if the tracker is guiding and aligned with the Sun.
        If so, return True, otherwise return False

        Parameters:
            THRESHOLD: amount (in deg) to require alt/az guider offset be within
        '''
        return self.is_guiding \
                and (self.guiding_offset_alt < THRESHOLD) and (self.guiding_offset_az < THRESHOLD)


    ############ PYRHELIOMETER ############
    # solar_irrad	read only	FLOAT
    # output_voltage	read only	FLOAT
    # heater_temp	read only	FLOAT
    # sensitivity	locked	FLOAT
    # clear_sky	read only	solar_irrad > X*clear_sky_model - exact threshold TBD


    ############ DOME ############
    # domeopen	read/write	BOOL
    # domeclose	read/write	BOOL
    # dome_in_motion	    read only	BOOL
    # tracker_online	    read only	checks if can `ping 192.168.23.242` and has active open connection at port 10001
    # pyrheliometer_online	read only	checks if can `ping 192.168.23.243` and has active open connection at port 502
    # enclosure_online	    read only	checks if can `ping 192.168.23.244` and has active open connection
    
    @property
    def domeopen(self):
        return self._domeopen
    
    @domeopen.setter
    def domeopen(self, val):
        self._domeopen = val

    @property
    def domeclosed(self):
        return self._domeclosed

    @domeclosed.setter
    def domeclosed(self, val):
        self._domeclosed = val

    def monitor_dome_in_motion(self):
        ''''
        Monitor the state of the dome while the motor current is nonzero
        Only return when the dome is dome moving

        Returns: dome_status (dict)
        '''
        dome_status = self.get_dome_status()
        while not (dome_status['Motor current'] == 0):
            self.dome_in_motion = True
            print('Dome in motion...')
            time.sleep(5)
            if not (dome_status['Dome state'] == 'Unknown'):
                print("Motor is running ({} A) but dome is {}! Stopping motor now...".format(dome_status['Motor current'], dome_status['Dome state']))
                self.dome.stop()
                print("Motor stopped.")
            time.sleep(0.5)
            dome_status = self.get_dome_status()
        print('Dome move complete.')
        self.dome_in_motion = False
        return dome_status

    def open_dome(self):
        '''
        Open the SoCal dome
        '''
        
        print('Opening SoCal dome...')
        self.dome.open()

        # Monitor dome status while it opens
        dome_status = self.monitor_dome_in_motion()
        self.domeopen(dome_status['Dome state'] == 'Open')
        self.domeclosed(dome_status['Dome state'] == 'Closed')
        assert dome_status['Motor current'] == 0, 'Motor is still running?'

        # If it got stuck in undefined state (e.g. if it stops partway open due to obstruction) tell it to close immediatley
        if dome_status['Dome state'] == 'Unknown':
            print('Dome did not open completely, closing now. Check limit switches and verify area around dome is clear of obstructions.')
            self.dome.stop()
            self.close_dome()

    def close_dome(self):
        '''
        Close the SoCal dome
        '''
        
        print('Closing SoCal dome...')
        self.dome.close()

        # Monitor dome status while it opens
        dome_status = self.monitor_dome_in_motion()
        self.domeopen(dome_status['Dome state'] == 'Open')
        self.domeclosed(dome_status['Dome state'] == 'Closed')
        assert dome_status['Motor current'] == 0, 'Motor is still running?'

        # If it got stuck in undefined state we have a problem
        if dome_status['Dome state'] == 'Unknown':
            self.dome.stop()
            print('Dome did not close completely. Physical assistance may be needed on the roof.')

    def get_dome_status(self):
        '''
        Get the current status of the various Dome sensors and parse
        '''
        
        status, response = self.dome.status()
        if response == '0 OK':
            # example status: "Closed,0,0,1,1,Stopped,0.0,Remote,Sensors:, Rain: off, Light: off, Power: on"
            domeopen, leftopen, rightopen, leftclose, rightclose, motorrunning, motorcurrent, opmode, _, rain, light, power = status.split(',')
            dome_status =  {'Dome state': domeopen, # ["Closed", "Unknown", "Open"]
                           'Left open switch' : bool(leftopen),  'Right open switch' : bool(rightopen), 
                           'Left close switch': bool(leftclose), 'Right close switch': bool(rightclose),
                           'Motor state': motorrunning, 'Motor current': float(motorcurrent),
                           'Operation mode': opmode, 
                           'Rain sensor' : rain.split('Rain:')[-1].strip(), 
                           'Light sensor': light.split('Light:')[-1].strip(), 
                           'Power sensor': power.split('Power:')[-1].strip(),
                          }
        elif response in self.dome.possible_responses:
            dome_status = status
            print('DOME ERROR:', response)
        else:
            dome_status = 'UNKNOWN'
            print('UNKNOWN DOME ERROR:', response)
        return dome_status