from labscript import *
from labscript_devices.PulseBlasterUSB import PulseBlasterUSB
import numpy as np

# Digital Device 
PulseBlasterUSB(name='pulseblaster_0', board_number=0, programming_scheme='pb_start/BRANCH')

# Clockline
ClockLine(name='pulseblaster_0_clockline', pseudoclock=pulseblaster_0.pseudoclock, connection='flag 0')



#Digital Ouput
DigitalOut('digiout_1',pulseblaster_0.direct_outputs, 'flag 1')
DigitalOut('digiout_2',pulseblaster_0.direct_outputs, 'flag 2')

# AnalogOut(name='anout_1', parent_device=pulseblaster_0,  connection='ao0')

################

# # Use a virtual, or 'dummy', device for the psuedoclock
# DummyPseudoclock(name='pseudoclock')

# # An output of this DummyPseudoclock is its 'clockline' attribute, which we use to trigger children devices
# DummyIntermediateDevice(name='pulseblaster_0.direct_outputs', parent_device=pulseblaster_0.pseudoclock)

# # # Create an AnalogOut child of the DummyIntermediateDevice
# AnalogOut(name='analog_out', parent_device=pulseblaster_0.direct_outputs, connection='ao0')




if __name__ == '__main__':
    # Begin issuing labscript primitives
    # start() elicits the commencement of the shot
    start()

    # Stop the experiment shot with stop()
    stop(1.0)

