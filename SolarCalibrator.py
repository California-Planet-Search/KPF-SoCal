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
              'DomeInMotion', # Dome is opening or closing 
              'ERROR_STATE',  # Undefined/error state 
             ]
    # Valid transitions between predefined SoCal operational states
    transitions = [
        {'trigger': 'power_on', 
            'source': 'PoweredOff', 'dest':'Stowed', 'before': 'power_on_system'},
        {'trigger': 'open', 
            'source': 'Stowed', 'dest':'DomeInMotion',
            'conditions': ['is_safe_to_open'], 'before': 'open_dome'},
        {'trigger': 'opened',
            'source': 'DomeInMotion', 'dest': 'OnSky', 'before': 'start_guiding'},
        {'trigger': 'stow',
            'source': 'OnSky', 'dest': 'DomeInMotion', 'before': 'close_dome'},
        {'trigger': 'stowed',
            'source': 'DomeInMotion', 'dest': 'Stowed', 'before': 'home_tracker'},
        {'trigger': 'power_off', 
            'source': 'Stowed', 'dest': 'PoweredOff', 'before': 'power_down_system'},
        {'trigger': 'errored',
            'source': '*', 'dest': 'ERROR_STATE'},
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
        # TODO: open connection to and read from pyrheliometer (write to file) 
        # TODO: verify pyrheliometer flux is reasonable
        # TODO: check current alt/az vs. predicted & guiding offset
        return True 

    def check_on_sun(self):
        # TODO: should this trigger anything else to happen (or not happen)?
        if self.on_sun:
            print('Guiding on Sun. Get yer photons here!')
        else:
            print("Guiding failed. If it's not cloudy, check the sun sensor alignment.")

    ########## TRANSITION DEFINITIONS ##########
    # Three stages to every transition
        # 1. precondition check: Is everything in order to make the transition?
        #   - Is the KTL service running?
        #   - Can the device be pinged? 
        #   - Weather/safety checks
        # 2. execution: make the transition by sending the corresponding commands
        #               to the appropriate devices
        # 3. postcondition check: Did the device(s) successfully transition?
        #   - If not, move to ERROR STATE

    def open_dome(self):
        ''' set domeopen True '''

        self.dispatcher.open_dome()
        
        # If the dome opened successfully, do transition "opened"
        if self.dispatcher.domeopen():
            self.opened()
        else:
            dome_status = self.dispatcher.get_dome_status()
            print('ERROR! The dome did not open. In fact, it is {}'.format(dome_status['Dome state']))
            self.errored()

    def close_dome(self):
        ''' set domeclosed True '''

        self.dispatcher.close_dome()
        
        # If the dome closed successfully, transition "closed"
        if self.dispatcher.domeclosed():
            self.closed()
        else:
            dome_status = self.dispatcher.get_dome_status()
            print('ERROR! The dome did not close. In fact, it is {}'.format(dome_status['Dome state']))
            self.errored()

    def start_guiding(self):
        # If the dome successfully opened, tell the tracker to start guiding
        # set guiding True
        print('Dome opened. Setting tracker to active guiding mode...')
        self.dispatcher.start_guiding()
        # Check that we're on-Sun
        self.check_on_sun()

    def home_tracker(self):
        # If the dome successfully closed, return the tracker to home
        print("Dome closed. Moving tracker to 'home'...")
        self.dispatcher.home_tracker()

    def power_down_system(self):
        # Turn off SoCal main power
        print('Powering off SoCal.')
    
    def power_on_system(self):
        # Turn on SoCal main power
        print('Powering on SoCal')