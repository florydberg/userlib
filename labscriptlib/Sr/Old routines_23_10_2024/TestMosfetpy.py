from labscript import start, stop
from generate_samples import generate_digital_samples, generate_analog_samples, test_word
from labscript_utils import import_or_reload
import_or_reload('labscriptlib.MOT.connection_table')

from labscriptlib.MOT.connection_table import *
from user_devices.mogdevice import MOGDevice

t=0
dt=board0.time_step #1mu second
usec=dt
us=usec
msec=1000*dt
ms=msec
sec=1000000*dt
s=sec
min=60*sec

start()

t+=dt
COILS_current.constant(t, 2)

t+=10*msec

for i in range(0,10):
    COILS_switch.go_high(t)#-------------CLOSE CIRCUIT
    t+=dt
    Freezer.constant(t,5)#flag
    

    t+=10*msec

    COILS_switch.go_low(t)#-------------OPEN CIRCUIT
    t+=dt
    Freezer.constant(t,0)#flag

    t+=10*msec
    i+=1

t+=dt
COILS_current.constant(t, 0)
t+=dt

t+=2*min #chilling time, enjoy

stop(t)
