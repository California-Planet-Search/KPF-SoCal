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
import numpy as np
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
            dome_status = self.get_dome_status()
            self._is_domeopen    = (dome_status['Status'] == 'Open')
            self._is_domeclosed  = (dome_status['Status'] == 'Closed')
            self._dome_in_motion = not (dome_status['Motor']['current'] == 0)
            self._dome_online    = self.dome.ws.connected
        except Exception as e:
            print('Unable to connect to DomeGuard at {}/{}'.format(dome.DOME_IP, dome.DOME_PORT))
            print(repr(e))
            self._dome_online = False

        # Try to open a connection to the tracker
        try:
            self.tracker = sun_tracker.EKOSunTracker()
            self._tracker_online = True
        except:
            print('Unable to connect to EKO Sun Tracker at {}/'.format(sun_tracker.TCP_IP, sun_tracker.TCP_PORT))
            self._tracker_online = False
        
        # KTL keywords with hardcoded default values
        self._is_slewing  = False
        self._alt_to_slew = None
        self._az_to_slew  = None
        self._solar_irrad        = 0
        self._pyr_output_voltage = 0
        self._pyr_heater_tem     = 0
        self._pyr_sensitivity    = 0
        self._clear_sky	         = 0    # solar_irrad > X*clear_sky_model - exact threshold TBD
        self._pyrheliometer_online = False  # self.pyrheliometer has connection

    ############################### EKO Sun Tracker Keywords ##############################
    @property
    def is_guiding(self):
        return self.tracking_mode == '3'

    @property
    def is_on_sun(self):
        time_in_waiting = 0
        while self.is_slewing:
            if time_in_waiting > 60:
                print("Timeout waiting for slew to end")
                return
            # wait until done slewing
            time.sleep(1)
            time_in_waiting += 1
        return not self.is_slewing and (self.tracking_mode == '3') # and irrad = nominal
        
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
    def is_slewing(self):
        return self._is_slewing

    @is_slewing.setter
    def is_slewing(self, new_is_slewing):
        self._is_slewing = new_is_slewing
    
    def slew(self):
        '''
        Slew the tracker, if `alt_to_slew` and `az_to_slew` are both set
        '''
        # TODO: if guiding and slew=false make it stop guiding?
        assert not self.is_slewing, 'Please wait until current slew is complete before sending a new slew command.'
        if (not self.az_to_slew is None) and (not self.alt_to_slew is None):
            self.is_slewing = True
            self.tracker.slew(self.alt_to_slew, self.az_to_slew)
            # Reset slew staging
            self.is_slewing = False
            self.alt_to_slew = None
            self.az_to_slew = None
        else:
            print('CANNOT SLEW: Must set both\nalt_to_slew: {}\naz_to_slew: {}'.format(self.alt_to_slew, self.az_to_slew))

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
        self._alt_to_slew = alt

    @property
    def az_to_slew(self):
        return self._az_to_slew
    
    @az_to_slew.setter
    def az_to_slew(self, az):
        '''
        Set the azimuth to move the tracker to.
        Will not slew until both `alt_to_slew` and `az_to_slew` 
        are  both set followed by a call to `set slew True`

        Args:
            az:  (float) azimuth in decimal degrees  (0 = South, 180 = North, +90 = East, -90 = West) TODO: verif E/W
        '''
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


    #################################### PYRHELIOMETER ####################################
    @property
    def solar_irrad(self):
        return self._solar_irrad

    @solar_irrad.setter
    def solar_irrad(self, irrad):
        self._solar_irrad = irrad

    @property
    def pyr_output_voltage(self):
        return self._pyr_output_voltage

    @pyr_output_voltage.setter
    def pyr_output_voltage(self, voltage):
        self._pyr_output_voltage = voltage

    @property
    def pyr_heater_temp(self):
        return self._pyr_heater_temp

    @pyr_heater_temp.setter
    def pyr_heater_temp(self, temperature):
        self._pyr_heater_temp = temperature

    @property
    def pyr_sensitivity(self):
        return self._pyr_sensitivity

    @pyr_sensitivity.setter
    def pyr_heater_temp(self, sensitivity):
        self._pyr_sensitivity = sensitivity

    @property	
    def clear_sky(self):
        return self._clear_sky	

    @clear_sky.setter
    def clear_sky(self, is_sky_clear):
        self._clear_sky = is_sky_clear

    ######################################## DOME ########################################
    @property
    def is_domeopen(self):
        return self._is_domeopen
    
    @is_domeopen.setter
    def is_domeopen(self, val):
        self._is_domeopen = val

    @property
    def is_domeclosed(self):
        return self._is_domeclosed

    @is_domeclosed.setter
    def is_domeclosed(self, val):
        self._is_domeclosed = val

    @property
    def dome_in_motion(self):
        return self._dome_in_motion

    @dome_in_motion.setter
    def dome_in_motion(self, val):
        self._dome_in_motion = val

    def monitor_dome_in_motion(self, direction):
        ''''
        Monitor the state of the dome while the motor current is nonzero
        Only return when the dome is dome moving

        Returns: dome_status (dict)
        '''
        # TODO: If received an error in get_dome_status need to throw an exception to halt the motion
        dome_status = self.get_dome_status()
        motor_status = dome_status['Motor']
        time_in_waiting = 0
        while motor_status['status'] == 'Stopped':
            if time_in_waiting >= 10:
                print('TIMEOUT -- Waited 10 seconds for dome to start moving.')
                self.dome.stop()
                return
            time.sleep(1)
            motor_status = self.get_dome_status()['Motor']
            time_in_waiting += 1

        assert motor_status['status'] == direction, 'Dome is {} but desired direction is {}'.format(motor_status['status'], direction)
        while not (motor_status['status'] == 'Stopped'):
            self.dome_in_motion = True
            print('Dome in motion: {}...'.format(dome_status['Motor']['status']))
            time.sleep(1)
            dome_status = self.get_dome_status()
            motor_status = dome_status['Motor']
        print('Dome move complete.')
        self.dome_in_motion = False
        return dome_status

    def open_dome(self):
        '''
        Open the SoCal dome
        '''
        
        print('Opening SoCal dome...')
        if self.is_domeopen:
            print('Dome is already open.')
            return

        self.dome.open()
 
        # Monitor the dome status as it opens
        dome_status = self.monitor_dome_in_motion('Opening')

        # When that concludes, confirm the dome opened
        self.is_domeopen   = (dome_status['Status'] == 'Open')
        self.is_domeclosed = (dome_status['Status'] == 'Closed')
        if self.is_domeopen and not self.is_domeclosed:
            print('Dome opened successfully.')
        elif  not self.is_domeopen and not self.is_domeclosed and (dome_status['Status'] == 'Unknown'):
            # If it got stuck in undefined state (e.g. if it stops partway open due to obstruction) tell it to close immediatley
            print('Dome did not open completely, closing now. Check limit switches and verify area around dome is clear of obstructions.')
            self.dome.stop()
            self.close_dome()
        else:
            print("Error: booleans don't match desired dome position")
            print('     Current state is {}.'.format(dome_status['Status']))
            print('     is_domeopen={} and is_domeclosed={}.'.format(self.is_domeopen, self.is_domeclosed))
            print("     Likely did not wait long enough before checking if dome started moving.")

    def close_dome(self):
        '''
        Close the SoCal dome
        '''
        
        print('Closing SoCal dome...')
        if self.is_domeclosed:
            print('Dome is already closed.')
            return

        self.dome.close()

        # Monitor the dome status as it closes
        dome_status = self.monitor_dome_in_motion('Closing')

        # When that concludes, confirm the dome closed
        self.is_domeopen   = (dome_status['Status'] == 'Open')
        self.is_domeclosed = (dome_status['Status'] == 'Closed')

        if self.is_domeclosed and not self.is_domeopen:
            print('Dome closed successfully.')
        elif  not self.is_domeopen and not self.is_domeclosed and (dome_status['Status'] == 'Unknown'):
            # If it got stuck in undefined state (e.g. if it stops partway open due to obstruction) tell it to close immediatley
            print('Dome did not close completely. Physical assistance may be needed on the roof. Trying again to close...')
            self.dome.stop()
            self.close_dome()
        else:
            print("Error: booleans don't match desired dome position")
            print('     Current state is {}.'.format(dome_status['Status']))
            print('     is_domeopen={} and is_domeclosed={}.'.format(self.is_domeopen, self.is_domeclosed))
            print("     Likely did not wait long enough before checking if dome started moving.")


    def get_dome_status(self, short=False):
        '''
        Get the current status of the various Dome sensors and parse
        '''
        result = self.dome.status(short=short)
        if result[-1] == self.dome.possible_responses[0]:
            status, response = result
            # example short status: 
            #     "Closed,0,0,1,1,Stopped,0.0,Remote,Sensors:, Power: on, Rain: off, Light: off"
            # Sensors can be in a random order!!!!
            if short:
                is_domeopen, leftopen, rightopen, leftclose, rightclose, motorrunning, motorcurrent, opmode, _, s1, s2, s3 = status.split(',')
                s1name, s1state = s1.split(':'); s2name, s2state = s2.split(':'); s3name, s3state = s3.split(':')
                sensors = {s1name.strip(): s1state.strip(), s2name.strip(): s2state.strip(), s3name.strip(): s3state.strip()}
                dome_status =  {'Status': is_domeopen, 'OP mode': opmode, 
                                'Limits': {'open left' : bool(leftopen),  'open right' : bool(rightopen), 
                                        'close left': bool(leftclose), 'close right': bool(rightclose)},
                                'Motor': {'status': motorrunning, 
                                        'current': float(motorcurrent)},
                                'Temperatures': {},
                                'Sensors': {'rain' : sensors['Rain'], 
                                            'light': sensors['Light'], 
                                            'power': sensors['Power']},
                            }
            else:            
                # Format into key-value pairs for dome_status dictionary
                s = status.replace('\n', ',')
                s = s.replace('Limits:', '').replace('Temperatures:','').replace('Sensors:,', '')
                s = s.replace('Guard', ',Guard').replace('Inside', ',Inside').replace('timeout', ',timeout')
                ds = {key.strip(): val.strip() for key, val in (pair.split(':') for pair in s[:-1].split(','))}
                # Reformat into appropriate datatypes
                dome_status =  {'Status': ds['Status'], 'OP mode': ds['OP mode'], 
                                'Limits': {key: {'ON': True, 'OFF': False}[ds[key]] 
                                        for key in ['open left', 'open right', 'close left', 'close right']},
                                'Motor': {'status': ds['Motor'], 
                                        'current': float(ds['actual current'].replace(' A', '')),
                                        'measured max': float(ds['measured max'].replace(' A', '')),
                                        'last overcurrent': np.nan if ds['last overcurrent']=='N/A' 
                                                                    else float(ds['last overcurrent'])},
                                'Temperatures': {'inside': float(ds['Inside'])*(9/5) + 32,
                                                'outside': float(ds['Outside'])*(9/5) + 32,
                                                'ebox'   : float(ds['Guard electronics'])*(9/5) + 32},
                                'Sensors': {'rain' : ds['Rain'], 
                                            'light': ds['Light'], 
                                            'power': ds['Power']},
                                'Watchdog': {'status': ds['Watchdog'], 
                                            'timeout' : ds['timeout']},
                                'Last command': ds['Last command']
                            }
        elif len(result) == 1 and result[0] in self.dome.possible_responses:
            response = result[0]
            dome_status = None
            print('DOME ERROR:', response)
        elif len(result) > 1 and result[-1] in self.dome.possible_responses:
            dome_status = result[0]
            response = result[-1]
            print('DOME ERROR', response)
        else:
            dome_status = 'UNKNOWN'
            response = 'UNKNOWN'
            print('UNKNOWN DOME ERROR - received: ', result)
        return dome_status

    #################################### CONNECTIVITY ####################################
    @property
    def tracker_online(self):
        try:
            _ = self.tracker.get_datetime() # connecton test
            self._tracker_online = True
        except:
            self._tracker_online = False

    @property
    def pyrheliometer_online(self):
        return True # TODO: check if pymodbus have a connected attribute?

    @property
    def dome_online(self):
        return self.dome.ws.connected