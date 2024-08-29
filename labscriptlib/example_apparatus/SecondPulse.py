from labscript import *
from labscript_devices.PulseBlasterUSB import PulseBlasterUSB
import time
from labscript_utils import import_or_reload
import_or_reload('labscriptlib.example_apparatus.connection_table')

from labscriptlib.example_apparatus.connection_table import *

#Begin issuing Labscript primitive
t=0
add_time_marker(t, "Start", verbose=True)
start()

period=0.1 #in sec
Ttot=10*period

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