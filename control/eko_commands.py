############################################################
#
#  eko_commands.py
#
#  Python wrappers for EKO Solar Tracker commands
#
#  Author: Ryan Rubenzahl
#  Last edit: 3/31/2022
#
############################################################
import time

# Global static variables
BUFFER_SIZE = 256 # Max number of bytes to read out
mode_description = {'0': 'Manual tracking mode', 
                    '1': 'Calculation tracking mode', 
                    '2': 'Sun-sensor tracking mode', 
                    '3': 'Sun-sensor with learning tracking mode'
                   }
error_msg = b'ERR\r'
success_msg = b'OK\r'

def send_command(command, tracker, wait_for_response=False):
    '''
    Sends command to the EKO tracker over TCP/IP 
    
    Args:
        command: string of EKO command. Must be cast to byte literal
                    e.g. b'TM\r' or with str.encode() (default is utf-8)
        tracker: socket object corresponding to the IP/port of the trackr
                    - SoCal Lantronix is 192.168.23.232
                    - Serial port 1 on Lantronix is Port 10001 (tracker, RS232)
        wait_for_response: (bool) wait for complete response from tracker before
                                    proceeding. Good for set commands (e.g. slew).

    Returns:
        response: string output from the tracker (decoded)
    '''

    print('Sending command: {}'.format(command))
    bytes_sent = tracker.send(command)
    print('Sent {} bytes'.format(bytes_sent))
    time.sleep(0.1)
    if wait_for_response: 
        complete_msg = [success_msg, error_msg]
        response = b''
        while not response in complete_msg: 
            response += tracker.recv(BUFFER_SIZE)
            time.sleep(1) # wait for complete response
    else:
        response = tracker.recv(BUFFER_SIZE)
    
    if response == error_msg:
        print('ERROR: command [{}] not recognized!'.format(command)) 
        return None
    else:
        return response.decode().strip('\r')



############################ SET commands ############################
def set_datetime(date, time):
    '''
    Set date and time (UTC) 

    Args:
        date: (string) date in YYYY-MM-DD format (e.g. '2020-09-16')
        time: (string) time in hh:mm:ss format   (e.g. '12:34:56')

    Returns:
        command: string formatted for EKO tracker to be used in send_command()
    '''
    YYYY, MM, DD = date.split('-')
    hh, mm, ss = time.split(':')
    command = 'TM,{},{},{},{},{},{}\r'.format(YYYY,MM,DD,hh,mm,ss).encode()
    return command


def set_location(lat, lon):
    '''
    Set location/site 

    Args:
        lat: (float) latitude in decimal degrees, + North, - South (e.g. 35.67199)
        lon: (float) longitude in decimal degrees, + East, - West (e.g. 139.67500) 

    Returns:
        command: string formatted for EKO tracker to be used in send_command()
    '''
    assert lat >= -90 and alt <= 90, 'Latitude {:.3f} outside limits [-90, 90] (+North, -South)'.format(alt)
    assert lon >= -180 and az <= 180, 'Longitude {:.3f} outside limits [-180, 180] (+East, -West)'.format(az)
    command = 'LO,{:+.5f},{:+.5f}\r'.format(lon, lat).encode()
    return command


def set_tracking_mode(mode):
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
        command: string formatted for EKO tracker to be used in send_command()
    '''
    mode_string = ''.join(['\n\t{}: {}'.format(m, mode_description[m]) for m in mode_description])
    assert mode in ['0', '1', '2', '3'], 'Invalid mode. Valid modes are: {}'.format(mode_string)
    command = 'MD,{}\r'.format(mode).encode()
    print('Setting active tracking mode to {} - {}'.format(mode, mode_description[mode]))
    return command


def set_position(alt, az):
    '''
    Set the tracker position (manual pointing).

    Args:
        alt: (float) altitude in decimal degrees (0 = Horizon, 90 = Zenith)
        az:  (float) azimuth in decimal degrees  (0 = South, 180 = North)

    Returns:
        command: string formatted for EKO tracker to be used in send_command()
    '''
    assert alt >= 0 and alt < 90, 'Alt {:.3f} outside limits [0, 90)'.format(alt)
    assert az >= -180 and az <= 180, 'Az {:.3f} outside limits [-180, 180]'.format(az)
    command = 'MP,{:.3f},{:.3f}\r'.format(az, alt).encode()
    return command


############################ GET commands ############################
def get_datetime(tracker):
    '''
    Get date and time (UTC) 

    Args:
        tracker: (socket object) socket TCP/IP port to read from

    Returns:
        datetime: datetime string formatted as YYYY-MM-DDThh:mm:ss 
    '''
    command = b'TM\r'
    print('Fetching date/time from tracker...')
    output = send_command(command, tracker)

    if output is None:
        return None
    else:
        YYYY, MM, DD, hh, mm, ss, ok = str(output).split(',')   
        datetime = '{}-{}-{}T{}:{}:{}'.format(YYYY, MM, DD, hh, mm, ss) 
        return datetime


def get_location(tracker):
    '''
    Get location/site latitude and longitude

    Args:
        tracker: (socket object) socket TCP/IP port to read from

    Returns:
        lat: (float) latitude in decimal degrees, + North, - South (e.g. 35.67199)
        lon: (float) longitude in decimal degrees, + East, - West (e.g. 139.67500) 
    '''
    command = b'LO\r'
    print('Fetching latitude/longitude from tracker...')
    output = send_command(command, tracker)

    if output is None:
        return None
    else:
        lon, lat, ok = output.split(',')
        lon = float(lon.replace(' ', ''))
        lat = float(lat.replace(' ', ''))
        return lat, lon 


def get_tracking_mode(tracker):
    '''
    Get active tracking mode. 

    Args:
        tracker: (socket object) socket TCP/IP port to read from
    
    Returns:
        mode: (str) tracking mode code
            0: Manual tracking mode
            1: Calculation tracking mode
            2: Sun-sensor tracking mode
            3: Sun-sensor with learning tracking mode
    '''
    command = b'MD\r'
    print('Fetching active tracking mode...')
    output = send_command(command, tracker)
    
    if output is None:
        return None
    else:
        mode, ok = output.split(',') 
        print('Current tracking mode: {} - {}'.format(mode, mode_description[mode]))
        return str(mode) 


def get_corrected_position(tracker):
    '''
    Get the current tracker position. 
    Corrected angle value means a calculated solar position with a 
    sun-sensor correction offset value. (Actual pointing angle)

    Args:
        tracker: (socket object) socket TCP/IP port to read from
    
    Returns:
        alt: (float) altitude in decimal degrees, + Upper, - Lower (e.g. 15.123)
        az:  (float) azimuth in decimal degrees, + West, - East, (e.g. 123.133)
    '''
    command = b'MR\r'
    print('Fetching current tracker position...')
    output = send_command(command, tracker)
    
    if len(output) == 0: # TODO: What is the right way to check if output? regex?
        return None
    else:
        az, alt, ok = output.split(',')
        az  = float(az.replace(' ', ''))
        alt = float(alt.replace(' ', ''))
        return alt, az 


def get_calculated_position(tracker):
    '''
    Get the calculated tracker position. 
    Calculated angle value means a calculated solar position 
    without a sun-sensor correction offset value

    Args:
        tracker: (socket object) socket TCP/IP port to read from
    
    Returns:
        alt: (float) altitude in decimal degrees, + Upper, - Lower (e.g. 15.123)
        az:  (float) azimuth in decimal degrees, + West, - East, (e.g. 123.133)
    '''
    command = b'CR\r'
    print('Fetching calculated tracker position...')
    output = send_command(command, tracker)
    
    if output is None:
        return None
    else:
        az, alt, ok = output.split(',')
        az  = float(az.replace(' ', ''))
        alt = float(alt.replace(' ', ''))
        return alt, az 


def get_sun_sensor_offset(tracker):
    '''
    Get the offset angle of the sun sensor (test only) 

    Args:
        tracker: (socket object) socket TCP/IP port to read from
    
    Returns:
        ha: (float) horizontal angle in decimal degrees
        va: (float) vertical angle in decimal degrees
    '''
    command = b'RO\r'
    print('Fetching sun sensor offset angle...')
    output = send_command(command, tracker)
    
    if output is None:
        return None
    else:
        ha, va, ok = output.split(',')
        ha = float(ha.replace(' ', ''))
        va = float(va.replace(' ', ''))
        return ha, va 


def get_firmware_version(tracker):
    '''
    Get the tracker firmware version 

    Args:
        tracker: (socket object) socket TCP/IP port to read from
    
    Returns:
        v: (str) firmware version (latest version as of May 15, 2003 is 3.00) 
    '''
    command = b'VER\r'
    print('Fetching tracker firmware version...')
    output = send_command(command, tracker)
    
    if output is None:
        return None
    else:
        v, ok = output.split(',')
        print('Tracker is running firmware version {}'.format(v))
        return v 
