# KPF-SoCal communication & control

The KPF Solar Calibrator has two main components which are controlled, the sun tracker itself and the enclosure in which it lives.

## EKO STR-22G Sun Tracker interface specifications

Communication is over RS-232, through Lantronix UDS2100 over ethernet. Serial commands wrapped in Python using `socket`.

=======
Lantronix IP: 192.168.23.242
Local port: 10001

|                |                     |
|:---------------|:--------------------|
|Interface       | RS-232C and RS-422  |
|Baud rate       | 9600 bps            |
|Data length     | 8 bit               |
|Parity          | None                |
|Stop bit        | 1 bit               |
|Flow control    | None                |

## Fornax Dome specifications

Communication is over WebSocket, through the DomeGuard computer over ethernet. Commands are
wrapped in python using `websockets`.

=======
DomeGuard IP: 192.168.23.244
WebServer port: 4030 
