power-monitor
Repository contains code for a Raspberry Pi running Python3 to connect
to an EKM Omnimeter 1v.3 power monitoring unit and to retrieve power
usage data from that unit. The data is collected at some periodic rate,
initially every minute, and written to adafruit.io to create a power
monitoring dashboard. The data monitored is total kWh consumed, amps 
and RMS volts on both lines of a 240V AC service and RMS Watts consumed
on both lines.

The rfomonitoring.py program is set up in init.d so that if the power
is interrupted to the RPi, the restart or reboot will start the program
up again and data will again be collected.

The RPi has a deadman daemon that sends a ping to a watchdog program 
every 10 seconds. If enough pings are not received, the watchdog program
resets the RPi, assuming that it is hung in some way.

The rfopower.py program imports the ekmmeters.py library of EKM interface
requests functions, the Adafruit_IO library of API requests to adafruit.io,
and the time and json libraries used to create delays between data reads
and to parse json data from the Omnimeter API calls.
