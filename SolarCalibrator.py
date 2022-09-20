############################################################
# 
#  SolarCalibrator.py
#
#  State machine to control overall SoCal operations by
#  definining valid states and how to move between them 
#
#  Author: Ryan Rubenzahl (rrubenza@caltech.edu)
#
############################################################

# import ktl
import time
from transitions import Machine
from transitions.extensions import GraphMachine # For visualizing the state machine

class SoCal(object):

    # SoCal operational states
    states = ['PoweredOff',     # Dome CLOSED and tracker stowed at 'home', powered OFF 
              'Stowed',         # Dome CLOSED and tracker stowed at 'home', powered ON 
              'Opening',        # Dome is OPENING
              'Open',           # Dome OPEN and tracker stowed at 'home'
              'AcquiringSun',   # Tracker is switched to active guiding mode and moving to the Sun
              'OnSky',          # Dome OPEN and tracker is in active guiding mode 
              'Closing',        # Dome is CLOSING
              'Closed',         # Dome CLOSED and tracker is in active guiding mode
              'StowingTracker', # Tracker is switched to manual pointing mode and moving to its 'home' position
              'ERROR',          # State to put SoCal in if one of the above transitions does not succeed
              'OFFLINE',        # At least one of the SoCal devices is offline/unreachable
              'RECOVERING',     # ERROR/OFFLINE is resolved and soCal is attempting to recover into the last defined state
             ]

    # Valid transitions between predefined SoCal operational states
    transitions = [
        # Power on the SoCal system
        {'trigger': 'power_on', 
            'source': 'PoweredOff', 'dest':'Stowed', 
            'prepare': 'can_power_on', 'before': 'power_on_system', 'after': 'did_power_on'},
        # Open the dome, while the tracker is homed. Only open if conditions are safe
        {'trigger': 'open', 
            'source': 'Stowed', 'dest':'Opening',
            'conditions':['operate', 'is_safe_to_open'], 
            'before': 'can_open', 'after': 'done_opening'},
            # After opening, check dome status and make next transition accordingly
            {'trigger': 'done_opening', 
                'source': 'Opening', 'dest':'Open', 'conditions':['operate', 'dome_is_open'], 'after': 'guide'},
            {'trigger': 'done_opening', 
                'source': 'Opening', 'dest':'ERROR', 'conditions':['operate', 'dome_not_open'], 'after': 'recover'},
        # With the dome open, enable active guiding on the solar tracker 
        {'trigger': 'guide',
            'source': 'Open', 'dest': 'AcquiringSun', 
            'conditions':['operate', 'is_safe_to_open'],
            'before': 'can_guide', 'after': 'done_acquiring'},
            # After acquiring, check guiding status and make next transition accordingly
            {'trigger': 'done_acquiring', 
                'source': 'AcquiringSun', 'dest':'OnSky', 'conditions':['operate', 'tracker_is_guiding']},
            {'trigger': 'done_acquiring', 
                'source': 'AcquiringSun', 'dest':'ERROR', 'conditions':['operate', 'tracker_not_guiding'], 'after': 'recover'},
        # OnSky guiding loop: during normal operations, this routinely checks weather status and sun altitude
        {'trigger': 'monitor_onsky', 
            'source': 'OnSky', 'dest':'OnSky', 'conditions':['operate', 'keep_observing'], 'after': 'wait'},
        {'trigger': 'monitor_onsky', 
            'source': 'OnSky', 'dest':'Closing', 'conditions':['operate', 'stop_observing'], 'before': 'can_close', 'after': 'done_closing'},
            # After closing, check dome status and make next transition accordingly
            {'trigger': 'done_closing', 
                'source': 'Closing', 'dest':'Closed', 'conditions':['operate', 'dome_is_closed'], 'after': 'stow'},
            {'trigger': 'done_closing', 
                'source': 'Closing', 'dest':'ERROR', 'conditions':['operate', 'dome_not_closed'], 'after': 'recover'},
        # With the dome closed, home the tracker
        {'trigger': 'stow',
            'source': 'Closed', 'dest': 'StowingTracker', 'before': 'can_stow', 'after': 'done_stowing'},
            # After stowing, check tracker status and make next transition accordingly
            {'trigger': 'done_stowing', 
                'source': 'StowingTracker', 'dest':'Stowed', 'conditions':['operate', 'tracker_is_home']},
            {'trigger': 'done_stowing', 
                'source': 'StowingTracker', 'dest':'ERROR', 'conditions':['operate', 'tracker_not_home'], 'after': 'recover'},
        # Power-down the SoCal system
        {'trigger': 'power_off', 
            'source': 'Stowed', 'dest': 'PoweredOff', 
            'prepare': 'can_power_off', 'before': 'power_down_system', 'after': 'did_power_off'},
        # If a device goes offline, transition to OFFLINE state
        {'trigger': 'offline', 'source': '*', 'dest': 'OFFLINE'},
        # If all devices come back online, enter RECOVERING state to attempt to transition back to last online state
        {'trigger': 'recover', 'source': 'OFFLINE', 'dest': 'RECOVERING',
            'after': 'did_recover',
        },
        {'trigger': 'recover', 'source': 'ERROR', 'dest': 'RECOVERING',
            'after': 'did_recover',
        },
    ]

    def __init__(self, graph=False):

        self.name = 'KPF Solar Calibrator'
        
        if graph:
            self.machine = GraphMachine(model=self, states=SoCal.states, show_conditions=True,
                                transitions=SoCal.transitions, initial='PoweredOff')     
        else: 
            # Connect to SoCal ktl service
            self.socal = ktl.Service ('kpfsocal')
    
            # Initialize the state machine
            self.machine = Machine(model=self, states=SoCal.states, transitions=SoCal.transitions, 
                                    initial=self.socal['LASTSTATE'].read())
        
        # Define functions to perform when entering each state
        self.machine.on_enter_Opening('open_dome')
        self.machine.on_enter_AcquiringSun('acquire_sun')
        self.machine.on_enter_OnSky('monitor_onsky')
        self.machine.on_enter_Closing('close_dome')
        self.machine.on_enter_StowingTracker('home_tracker')
        # self.machine.on_enter_OFFLINE('go_offline')
        self.machine.on_enter_RECOVERING('try_recover')

    ################################# CONDITION DEFINITIONS #################################
    @property
    def operate(self):
        """ If True, SoCal runs in autonomous mode. if False, prevents state transitions from occuring. """
        # return self.socal['OPERATE'].read()
        return True

    @property
    def is_safe_to_open(self):
        """ Verify conditions are safe to open """
        return self.socal['WXSAFE'].read()

    @property
    def keep_observering(self):
        """ Verify conditions are good to keep observing """
        return (self.socal['WXSAFE'].read()) and (self.socal['SUNALT'].read() >= 30)
    
    @property
    def stop_observing(self):
        """ Check if weather is unsafe or if day has ended """
        return not self.keep_observing()
    
    @property
    def tracker_is_guiding(self):
        """ Verify tracker is guiding on the Sun """
        # return (self.socal['EKOMODE'].read() == '3') # TODO: and OFFSETALT is nominal and OFFSETAZ is nominal
        if self.socal['EKOGUIDING'].read():
            print('Guiding on Sun. Get yer photons here!')
        else:
            print("Guiding failed. If it's not cloudy, check the sun sensor alignment.")


    @property
    def tracker_not_guiding(self):
        """ Check that the tracker is not guiding on the Sun """
        return not self.tracker_is_guiding()
    
    @property
    def dome_is_open(self):
        """ Check that the enclosure is open """
        if self.socal['ENCSTATUS'].read() == "Open":
            return True
        else:
            print('ERROR! The dome did not open. In fact, it is {}'.format(self.socal['ENCSTATUS'].read()))

    @property
    def dome_not_open(self):
        """ Check if enclosure is not open """
        return not self.dome_is_open()
    
    @property
    def dome_is_closed(self):
        """ Check that the enclosure is closed """
        if self.socal['ENCSTATUS'].read() == "Closed":
            return True
        else:
            print('ERROR! The dome did not close. In fact, it is {}'.format(self.socal['ENCSTATUS'].read()))
               
    @property
    def dome_not_closed(self):
        """ Check if enclosure is not closed """
        return not self.dome_is_closed()
    
    @property
    def tracker_is_home(self):
        """ Verify tracker is in 'home' position """
        # current_alt = self.socal['EKOALT'].read()
        # current_az  = self.socal['EKOAZ'].read()
        # track_mode  = self.socal['EKOMODE'].read()
        # return (current_alt == 0) and (current_az == 0) and (track_mode == '0')
        return self.socal['EKOHOME'].read()
    
    @property
    def tracker_not_home(self):
        """ Check that the tracker is not guiding on the Sun """
        return not self.tracker_is_home()

    ################################# TRANSITION DEFINITIONS #################################
    # Three stages to every transition
        # 1. precondition: Is everything in order to make the transition?
        #   - Is the KTL service running?
        #   - Can the device be pinged? 
        #   - Weather/safety checks
        # 2. perform: make the transition by sending the corresponding commands
        #               to the appropriate devices
        # 3. postcondition: Did the device(s) successfully transition?
        #   - If not, move to ERROR STATE

    ############################ power_on: PoweredOff --> Stowed ############################
    def can_power_on(self):
        # Precondition check for transition `power_on`
        # TODO
        return True

    def power_on_system(self):
        # Turn on SoCal main power
        # TODO
        print('Powering on SoCal')

    def did_power_on(self):
        # Postcondition check for transition `power_on`
        # TODO
        return True

    ############################ open: Stowed --> Opening ############################
    def can_open(self):
        ''' Verify we can communicate with the enclosure '''
        return self.socal['ENCONLINE'].read()

    def open_dome(self):
        ''' Send command to DomeGuard to open the enclosure '''
        self.socal['ENCCMD'].write('open')
        
    ############################ guide: Opening --> OnSky ############################
    def can_guide(self):
        ''' Verify we can communicate with the sun tracker '''
        return self.socal['EKOONLINE'].read()

    def acquire_sun(self):
        ''' set tracking_mode 3 '''
        print('Setting tracker to active guiding mode...')
        self.socal['EKOCMD'].write('guide') # self.socal['EKOMODE'].write('3')

    def wait(self):
        ''' wait a few seconds so we don't have a super-fast internal loop '''
        time.sleep(5)
        
    ############################ close: OnSky --> Closing ############################
    def can_close(self):
        ''' Verify we can communicate with the enclosure '''
        return self.socal['ENCONLINE'].read()

    def close_dome(self):
        ''' Send command to DomeGuard to open the enclosure '''
        self.socal['ENCCMD'].write('close')

    ############################ stow: Closing --> Stowed ############################
    def can_stow(self):
        ''' Verify we can communicate with the sun tracker '''
        return self.socal['EKOONLINE'].read()

    def home_tracker(self):
        ''' Tell the tracker to point back to its 'home' position '''
        print("Dome closed. Moving tracker to 'home'...")
        self.socal['EKOCMD'].write('stow')
        # self.socal['EKOSETALT'].write(0.0)
        # self.socal['EKOSETAZ'].write(0.0)
        # self.socal['EKOSLEW'].write(True)

    ############################ close: Stowed --> PoweredOff ############################
    def can_power_off(self):
        # Precondition check for transition `power_off`
        return True

    def power_down_system(self):
        # Turn off SoCal main power
        print('Powering off SoCal.')

    def did_power_off(self):
        # Postcondition check for transition `power_off`
        return True

    ############################ offline: * --> OFFLINE ############################

    def go_offline(self):
        ''' If the something goes offline, close the dome for safety '''
        if self.can_close():
            self.close_dome()

            if self.dome_not_closed():
                print('ERRROR: Dome did not close!')
        else:
            print('ERRROR: Cannot close dome!')
            
    ############################ recover: OFFLINE --> RECOVERING ############################

    def try_recover(self):
        ''' Figure out what state SoCal was in when it went offline, and try to re-establish that state '''
        if self.socal['ENCSTAT'].read() == 'Open' and self.socal['EKOMODE'] == '3':
            # force transition to OnSky
            self.to_OnSky()
        elif self.socal['ENCSTAT'].read() == 'Open' and self.socal['EKOHOME'].read():
            # force transition to Open
            self.to_Open()
        elif self.socal['ENCSTAT'].read() == 'Closed' and not self.socal['EKOHOME'].read():
            # force transition to Closed
            self.to_Closed()
        else:
            # Try to restore tracker and dome to stowed/closed positions
            try:
                self.socal['ENCCMD'].write('close')
                self.socal['EKOCMD'].write('home')        
                self.to_Stowed()
            except Exception as e:
                print(e)
        
    def did_recover(self):
        ''' Verify self.state is consistent with ENCSTATUS and EKOMODE/EKOHOME '''
        encstatus = self.socal['ENCSTATUS'].read()
        ekomode   = self.socal['EKOMODE'].read()
        ekohome   = self.socal['EKOHOME'].read()

        device_status = {'Stowed': ('Closed', '0', True),
                         'Closed': ('Closed', '3', False),
                         'Open'  : ('Open', '3', True),
                         'OnSky' : ('Open', '3', False),
                        }
                        
        return device_status[str(self.state)] == (encstatus, ekomode, ekohome)