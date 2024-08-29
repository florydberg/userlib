from labscript import *
from labscript_devices.PulseBlasterUSB import PulseBlasterUSB
from labscript import start, stop
from labscript_utils import import_or_reload
import_or_reload('labscriptlib.example_apparatus.connection_table')

from labscriptlib.example_apparatus.connection_table import *



# t = board0.start_time
# dt =100000*board0.time_step #mu seconds
# Ttot=100*dt


t=0
period=4 #in sec
Ttot=5*period


add_time_marker(t, "Start", verbose=True)

start()


while t < Ttot:

    pb0_trg.go_high(t)

    digiout_1.go_low(t)
    digiout_2.go_high(t)

    pokemon1.go_high(t)
    digimon1.go_high(t)

    t+=period/4

    digiout_1.go_high(t)
    digiout_2.go_low(t)

    # pokemon1.go_low(t)
    # digimon1.go_low(t)

    t+=period/4

    digiout_1.go_low(t)
    digiout_2.go_high(t)

    # pokemon1.go_high(t)
    # digimon1.go_high(t)

    t+=period/4

    digiout_1.go_high(t)
    digiout_2.go_low(t)

    pokemon1.go_low(t)
    digimon1.go_low(t)

    pb0_trg.go_low(t)

    t+=period/4

digiout_1.go_low(t)
digiout_2.go_low(t)

stop(t+period/4)