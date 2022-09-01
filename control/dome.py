############################################################
# 
#  dome.py
#
#  Object/functions for controlling the SoCal dome 
#
#  Author: Ryan Rubenzahl
#  Last edit: 8/25/2022
#
############################################################

import websocket

DOME_IP = "192.168.23.244"
DOME_PORT = "4030"

class DougDimmadome(object):

    possible_responses = ["0 OK",
                          "1 Rejected. Unknown command",
                          "2 Rejected. Operation mode switch is in local mode",
                          "3 Rejected. Switches on both ends are ON",
                          "4 Rejected. System is running on battery",
                          "5 Rejected. No Current sensor is present",
                          "6 Rejected. Invalid output name",
                          "7 Rejected. Operation blocked by sensor"
                         ]

    def __init__(self):
        self.wsPath = "ws://{}:{}/ws".format(DOME_IP, DOME_PORT)
        self.connect_ws()

    def connect_ws(self):
        """ Open the WebSocket connection """
        self.ws = websocket.WebSocket()
        self.ws.connect(self.wsPath)
        self.ws.settimeout(60)
        print('Opened WebSocket at {}'.format(self.wsPath))

    def close_ws(self):
        """ Close the WebSocket connection """
        self.ws.close()
        if not self.ws.connected:
           print('Closed WebSocket connection at {}.'.format(self.wsPath))
        else:
            print('WebSocket connection failed to close.')

    def __execCommands(self, cmd):
        """ Send command to the DomeGuard and recieve response """
        self.ws.send(cmd)
        result = [self.ws.recv()]
        while not result[-1] in self.possible_responses:
            result.append(self.ws.recv())
        return result
                
    def open(self):
        """ Open the dome """
        return self.__execCommands("open")

    def close(self):
        """ Close the dome """
        return self.__execCommands("close")
    
    def stop(self):
        """ Halt the dome motor """
        return self.__execCommands("stop")
    
    def status(self, short=False, verbose=False):
        """ Check the status of the dome """
        if not short:
            result = self.__execCommands("status")
            if verbose and result[-1] == self.possible_responses[0]:
                print(result[0])
        else:
            status, response = self.__execCommands("s")
            if verbose and result[-1] == self.possible_responses[0]:
                print(result[0])
        return result

    def set_ch1(self, state):
        """
        Set the state of the output relay

        Parameters: 
            state ["on", "off"]
        """
        assert state in ['on', 'off']
        cmd = 'set ch1 {}'.format(state)
        return self.__execCommands(cmd)
