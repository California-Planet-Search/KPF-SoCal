# KPF-SoCal telemtry

Code for sending/recieving commands to the solar tracker.

Communication is over RS-232, through Lantronix into ethernet

Lantronix: 192.168.23.232
Local port: 10001 (EKO Tracker)
Local port: 10002 (Pyrheliometer)

Serial commands wrapped in Python using [`socket`][https://docs.python.org/3/library/socket.html]

Communication with Keck via the Keck Task Library (KTL) using [`ktl`][http://spg.ucolick.org/KTLPython/] 

## EKO Solar Tracker Interface specifications

|                |                     |
|:---------------|:--------------------|
|Interface       | RS-232C and RS-422  |
|Baud rate       | 9600 bps            |
|Data length     | 8 bit               |
|Parity          | None                |
|Stop bit        | 1 bit               |
|Flow control    | None                |
