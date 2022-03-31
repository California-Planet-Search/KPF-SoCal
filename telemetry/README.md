# KPF-SoCal telemtry

Code for sending/recieving commands to the solar tracker.

Communication is over RS-232, through Lantronix UDS2100 over ethernet.

Serial commands wrapped in Python using `socket`.

Communication with Keck via the Keck Task Library (KTL) using [`KTLPython`][http://spg.ucolick.org/KTLPython/]

=======
Lantronix: 192.168.23.232
Local port: 10001 (EKO Tracker)

## EKO Solar Tracker Interface specifications

|                |                     |
|:---------------|:--------------------|
|Interface       | RS-232C and RS-422  |
|Baud rate       | 9600 bps            |
|Data length     | 8 bit               |
|Parity          | None                |
|Stop bit        | 1 bit               |
|Flow control    | None                |
