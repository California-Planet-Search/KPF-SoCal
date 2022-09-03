############################################################
# 
#  SolarCalibrator.py
#
#  State machine to control overall SoCal operations by
#  definining valid states and how to move between them 
#
#  Author: Ryan Rubenzahl
#
############################################################

import Dispatcher
from transitions import Machine
from transitions.extensions import GraphMachine # For visualizing the state machine
# from irradiance import log_irrad # TODO: rewrite function to work in this context

class SoCal(object):

    # SoCal operational states
    states = ['PoweredOff',   # Tracker stowed at 'home' & dome CLOSED, powered OFF 
              'Stowed',       # Tracker stowed at 'home' & dome CLOSED, powered ON 
              'OnSky',        # Dome OPEN and tracker is in active guiding mode 
              'Opening',      # Dome is opening
              'Closing',      # Dome is closing
            #   'ERROR_STATE',  # Undefined/error state 
             ]
    # Valid transitions between predefined SoCal operational states
    transitions = [
        {'trigger': 'power_on', 
            'source': 'PoweredOff', 'dest':'Stowed', 
            'prepare': 'can_power_on', 'before': 'power_on_system', 'after': 'did_power_on'},
        {'trigger': 'open', 
            'source': 'Stowed', 'dest':'Opening',
            'conditions': ['is_safe_to_open'], 
            'before': 'can_open', 'after': 'did_open'},
        {'trigger': 'guide',
            'source': 'Opening', 'dest': 'OnSky', 
            'prepare': 'can_guide', 'before': 'start_guiding', 'after': 'are_guiding'},
        {'trigger': 'close',
            'source': 'OnSky', 'dest': 'Closing', 
            'before': 'can_close', 'after': 'did_close'},
        {'trigger': 'stow',
            'source': 'Closing', 'dest': 'Stowed', 
            'prepare': 'can_stow', 'before': 'stow_tracker', 'after': 'did_stow'},
        {'trigger': 'power_off', 
            'source': 'Stowed', 'dest': 'PoweredOff', 
            'prepare': 'can_power_off', 'before': 'power_down_system', 'after': 'did_power_off'},
        # {'trigger': 'errored', 'source': '*', 'dest': 'ERROR_STATE'},
        ]

    def __init__(self, graph=False):
            
        # Initialize the state machine
        self.name = 'KPF Solar Calibrator'
        if graph:
            self.machine = GraphMachine(model=self, states=SoCal.states, show_conditions=True,
                                transitions=SoCal.transitions, initial='PoweredOff')
        else:
            self.machine = Machine(model=self, states=SoCal.states,
                                transitions=SoCal.transitions, initial='PoweredOff')
        
        # Transition functions
        self.machine.on_enter_Opening('open_dome')
        self.machine.on_enter_Closing('close_dome')
        
        # Connect to the dispatcher
        self.dispatcher = Dispatcher.connect()
        
    @property
    def is_safe_to_open(self):
        """ Verify conditions are safe to open """
        # TODO: weather check (rain sensor/etc.) 
        return True 
    
    @property
    def on_sun(self):
        """ Check that the tracker is pointed at the Sun """
        # Should this move to Dispatcher.py?
        # TODO: open connection to and read from pyrheliometer (write to file) 
        # TODO: verify pyrheliometer flux is reasonable
        # TODO: check current alt/az vs. predicted & guiding offset
        return True 

    def check_on_sun(self):
        if self.dispatcher.is_on_sun:
            print('Guiding on Sun. Get yer photons here!')
        else:
            print("Guiding failed. If it's not cloudy, check the sun sensor alignment.")

    ################################# TRANSITION DEFINITIONS #################################
    # Three stages to every transition
        # 1. precondition check: Is everything in order to make the transition?
        #   - Is the KTL service running?
        #   - Can the device be pinged? 
        #   - Weather/safety checks
        # 2. execution: make the transition by sending the corresponding commands
        #               to the appropriate devices
        # 3. postcondition check: Did the device(s) successfully transition?
        #   - If not, move to ERROR STATE

    ############################ power_on: PoweredOff --> Stowed ############################
    def can_power_on(self):
        # Precondition check for transition `power_on`
        return True

    def power_on_system(self):
        # Turn on SoCal main power
        print('Powering on SoCal')

    def did_power_on(self):
        # Postcondition check for transition `power_on`
        return True

    ############################ open: Stowed --> Opening ############################
    def can_open(self):
        # Precondition check for transition `open`
        return self.dispatcher.dome_online

    def open_dome(self):
        ''' set domeopen True '''
        self.dispatcher.open_dome()

    def did_open(self):
        # Postcondition check for transition `open`
        # If the dome opened successfully, do transition 'guide'
        if self.dispatcher.is_domeopen:
            self.guide()
        else:
            dome_status = self.dispatcher.get_dome_status()
            print('ERROR! The dome did not open. In fact, it is {}'.format(dome_status['Dome state']))
            # self.errored()

    ############################ guide: Opening --> OnSky ############################
    def can_guide(self):
        # Precondition check for transition `guide`
        # ping tracker
        return self.dispatcher.tracker_online

    def start_guiding(self):
        ''' set tracking_mode 3 '''
        print('Dome opened. Setting tracker to active guiding mode...')
        self.dispatcher.is_slewing = True
        self.dispatcher.tracking_mode = '3'
        self.dispatcher.is_slewing = False
        
    def are_guiding(self):
        # Postcondition check for transition `guide`
        self.check_on_sun() # TODO

    ############################ close: OnSky --> Closing ############################
    def can_close(self):
        # Precondition check for transition `close`
        return self.dispatcher.dome_online

    def close_dome(self):
        ''' set domeclosed True '''
        self.dispatcher.close_dome()

    def did_close(self):
        # Postcondition check for transition `close`
        if self.dispatcher.is_domeclosed:
            self.stow()
        else:
            dome_status = self.dispatcher.get_dome_status()
            print('ERROR! The dome did not close. In fact, it is {}'.format(dome_status['Status']))
            # self.errored()    
               
    ############################ stow: Closing --> Stowed ############################
    def can_stow(self):
        # Precondition check for transition `stow`
        return self.dispatcher.tracker_online

    def stow_tracker(self):
        # If the dome successfully closed, return the tracker to home
        print("Dome closed. Moving tracker to 'home'...")
        self.dispatcher.alt_to_slew = self.dispatcher.tracker.HOME_ALT
        self.dispatcher.az_to_slew  = self.dispatcher.tracker.HOME_AZ
        self.dispatcher.slew()

    def did_stow(self):
        # Postcondition check for transition `stow`
        # confirm tracker pointing at home
        return self.dispatcher.current_alt == 0 and self.dispatcher.current_az == 0 and self.dispatcher.tracking_mode == '0'

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