############################################################
#
#  commands.py
#
#  Python wrappers for Solar Tracker commands/routines
#
#  Author: Ryan Rubenzahl
#  Last edit: 9/16/2020
#
############################################################

from eko_commands import *

def send_command(command, ser):
    '''
    Sends command to the serial port provided
    
    Args:
        command: string of EKO command. Must be cast to byte literal
                    e.g. b'TM\r' or with encode (default is utf-8)
        ser: pyserial object of the serial port to send the command to

    Returns:
        output: string output from the tracker
    '''

    print('Sending command: {}'.format(command))

    bytes_written = ser.write(command)
    print('Wrote {} bytes'.format(bytes_written))

    bytes_recieved = ser.in_waiting
    print('Recieved {} bytes'.format(bytes_recieved))

    output = ser.read(bytes_recieved).decode().strip('\r')
    if output == 'ERR':
        print('ERROR: command [{}] not recognized!'.format(command)) 
        return None
    else:
        return output


def slew(ser, alt, az):
    '''
    Switches to manual pointing and slews the tracker to the desired position 
    
    Args:
        ser: pyserial object of the serial port to send the command to
        alt: (float) altitude in decimal degrees to slew to (e.g. 15.123)
        az:  (float) azimuth in decimal degrees to slew to (e.g. 123.133)

    Returns:
        alt: (float) tracker altitude in decimal degrees (e.g. 15.123)
        az:  (float) tracker azimuth in decimal degrees (e.g. 123.133)
    '''
    # 1. Set the tracker to “Manual command mode”
    cmd = set_tracking_mode(0)
    output = send_command(cmd, ser)
    if output is None:
        return
    else:
        print(output)

    # 2. Set a pointing direction
    cmd = set_position(alt, az)
    output = send_command(cmd, ser)
    if output is None:
        return
    else:
        print(output)
    
    # 3. Read the current pointing position
    output =  get_corrected_position(ser)
    if output is None:
        return
    else:
       alt, az = output
       print('Now pointing at\n\tAlt = {:.3f}\n\tAz = {:.3f}'.format(alt, az))

    if keep_manual:
        return
    else:
        cmd = set_tracking_mode(3)
        output = send_command(cmd, ser)
        if output is None:
            return
        else:
            print(output)

