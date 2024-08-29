from labscript import *
from labscript_devices.PulseBlasterUSB import PulseBlasterUSB

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


digiout_1.go_low(t+0.5)
digiout_2.go_low(t)

t+=1

digiout_1.go_high(t)
digiout_2.go_high(t+0.5)

t+=1

digiout_1.go_low(t)
digiout_2.go_low(t)

#Stop Experiment shot with stop
stop(t)