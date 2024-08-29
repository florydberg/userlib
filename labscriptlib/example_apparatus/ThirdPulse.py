from labscript import *
from labscript_devices.PulseBlasterUSB import PulseBlasterUSB
import time

# Digital Device 
PulseBlasterUSB(name='pulseblaster_0', board_number=0, programming_scheme='pb_start/BRANCH')

# Clockline
ClockLine(name='pulseblaster_0_clockline', pseudoclock=pulseblaster_0.pseudoclock, connection='flag 0')

#Digital Ouput
DigitalOut('digiout_1',pulseblaster_0.direct_outputs, 'flag 1')
DigitalOut('digiout_2',pulseblaster_0.direct_outputs, 'flag 2')

#Begin issuing Labscript primitive
t=0
add_time_marker(t, "Start", verbose=True)
start()

period=0.01 #in sec
Ttot=1000*period

while t < Ttot:

    digiout_1.go_low(t)
    digiout_2.go_high(t)

    t+=period/2

    digiout_1.go_high(t)
    digiout_2.go_low(t)

    t+=period/2

digiout_1.go_low(t)
#Stop Experiment shot with stop
stop(t)