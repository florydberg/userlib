from labscript import start, stop
from generate_samples import generate_digital_samples, generate_analog_samples, test_word
from labscript_utils import import_or_reload
import_or_reload('labscriptlib.example_apparatus.connection_table')

from labscriptlib.example_apparatus.connection_table import *
from user_devices.mogdevice import MOGDevice

# t = board0.start_time
t=0
dt=board0.time_step #1mu second
us=dt
ms=1000*dt
s=1000000*dt
start()


trg_osc.go_high(t)
t+=dt

i=0
while i < 10:

    COILS.constant(t, 3.1)
    t+=dt
    MOT_2D_trg.go_high(t)
    MOT_3D_trg.go_high(t)

    t+=90*ms

    COILS.constant(t-dt, 0)
    t+=dt
    MOT_2D_trg.go_low(t)
    MOT_3D_trg.go_low(t)

    t+=10*ms

    i=i+1

trg_osc.go_low(t)


MOT_2D_trg.go_high(t)
MOT_3D_trg.go_high(t)

t+=s
stop(t)
