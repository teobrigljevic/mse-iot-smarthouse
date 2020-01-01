# ACTUASIM

The aim of Actuasim is to reproduce a very simple building KNX automation.
It can be used to reproduce an existing building, in order to develop the KNX automation without disturbing people in their offices.
It replaces a KNXnet/IP gateway, handles all received datagram and triggers the corresponding actions. And as much as the real building, blinds and valves positions can be set by the user as well.


# USAGE
The program is written in Python3, and depends on:

- [Knxnet](https://githepia.hesge.ch/adrienma.lescourt/knxnet_iot)

- [PyQt5](https://riverbankcomputing.com/software/pyqt)

Simply execute `python actuasim.py` to start the application.


Once launched, Actuasim will load a file **saved\_rooms.json** containing the building configuration with all the KNX addresses
(if this file does not exist, it is created with a default configuration composed of 2 rooms, each one has 2 blinds and two radiator valves.)

Whenever the application is closed, the building configuration with the current position of blinds and valves are stored in this **saved\_rooms.json** file.

You can edit this it to set up your specific building configuration.

By default, Actuasim is listening on UDP port 3671.

A **actuasim.log** file is written to monitor every received frame or event with the decoded data.



# REPRODUCED HARDWARE

- **Blind**: Tunneling data can bea  boolean and will order the blind to move 1=Down or 0=Up, or a byte with direct blind position

- **Radiator valve**: Tunneling data is one byte, the direct valve position
