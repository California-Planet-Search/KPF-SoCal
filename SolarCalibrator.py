############################################################
# 
#  SolarCalibrator.py
#
#  State machine to control overall SoCal operations by
#  definining valid states and how to move between them 
#
#  Author: Ryan Rubenzahl
#  Last edit: 8/25/2022
#
############################################################

from transitions import Machine
# from irradiance import log_irrad # TODO: rewrite function to work in this context
from control import dome, sun_tracker

class SoCal(object):

    # SoCal operational states
    states = ['Powered off',    # Tracker stowed at 'home' & dome CLOSED, powered OFF 
              'Stowed',         # Tracker stowed at 'home' & dome CLOSED, powered ON 
              'On-sky',         # Dome OPEN and tracker is in active guiding mode 
              'Dome in motion', # Dome is opening or closing 
              'ERROR STATE',    # Undefined/error state 
             ]

    # Valid transitions between predefined SoCal operational states
    transitions = [
        {'trigger': 'power_on',
            'source': 'Powered off', 'dest':'Stowed'},
        {'trigger': 'open',     
            'source': 'Stowed', 'dest':'Dome in motion',
            'conditions': ['is_safe_to_open'], # only open if safe to do so
            'after': ['check_opened']},
        {'trigger': 'opened',
            'source': 'Dome in motion', 'dest': 'On-sky',
            'after': ['check_on_Sun']}, # and afterwards, verify that we're on-Sun
        {'trigger': 'close',
            'source': 'On-sky', 'dest': 'Dome in motion'},
        {'trigger': 'closed',
            'source': 'Dome in motion', 'dest': 'Stowed'},
        {'trigger': 'power_off', 
            'source': 'Stowed', 'dest': 'Powered off'},
        {'trigger': 'errored',
            'source': '*', 'dest': 'ERROR STATE'},
        ]

    def __init__(self):

        # Initialize the state machine
        self.machine = Machine(model=self, states=SoCal.states, 
                               transitions=SoCal.transitions, initial='Powered off')

    @property
    def is_safe_to_open(self):
        """ Verify conditions are safe to open """
        # TODO: weather check (rain sensor/etc.) 
        return True 
    
    @property
    def on_Sun(self):
        """ Check that the tracker is pointed at the Sun """
        # TODO: read pyrheliometer & check current alt/az vs. predicted & guiding offset
        return True 

    def check_on_Sun(self):
        # TODO: should this trigger anything else to happen (or not happen)?
        if self.on_Sun:
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

    def on_open(self):
        # TODO: Tell dome to open
        print('Opening SoCal dome...')
        self.dome_status()

    def on_close(self):
        # TODO: Tell dome to close
        print('Closing SoCal dome...')
        self.dome_status()

    def dome_status(self):
        opened = True # TODO: Return dome.status and verify opened
        closed = False # TODO: Return dome.status and verify closed
        undef  = not opened and not closed # Dome partway open?
        if opened:
            self.opened()
        elif closed:
            self.closed()
        else:
            print('ERROR! The dome did not open.')
            self.errored()

    def on_opened(self):
        # If the dome successfully opened, tell the tracker to start guiding
        # Wait until tracker is done moving (check alt/az or simply wait for serial recv?)
        print('Opened, setting tracker to active guiding mode...')

    def on_closed(self):
        # If the dome successfully closed, return the tracker to home
        print("Closed, moving tracker to 'home'...")

    def on_power_on(self):
        # Turn on SoCal main power
        print('Powering down SoCal.')
        return
    
    def on_power_off(self):
        # Turn off SoCal main power
        print('Powering on SoCal')
        return
