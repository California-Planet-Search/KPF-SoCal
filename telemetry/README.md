# KPF-SoCal telemtry

Code for sending/recieving commands to the solar tracker.

Communication is over RS-232 to USB2.0

Serial commands wrapped in Python using [`pySerial`][https://pyserial.readthedocs.io/en/latest/pyserial.html]

Communication with Keck via the Keck Task Library (KTL) using [`ktl`][http://spg.ucolick.org/KTLPython/] (Requires Python 2.0)

## EKO Solar Tracker Interface specifications

|                |                     |
|:---------------|:--------------------|
|Interface       | RS-232C and RS-422  |
|Baud rate       | 9600 bps            |
|Data length     | 8 bit               |
|Parity          | None                |
|Stop bit        | 1 bit               |
|Flow control    | None                |
