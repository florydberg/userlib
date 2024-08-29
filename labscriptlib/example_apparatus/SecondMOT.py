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

if True:
    # Connect to device
    dev = MOGDevice('192.168.1.100')
    print('Device info:', dev.ask('info'))

    channel = 1  # channel 1-4
    frequency = 200.0  # frequency in MHz
    amp = [-10.0, 0.0]  # [minimum,maximum,step] amplitude in dBm


    dev.cmd('OFF,1')
    t=+2*dt
    dev.cmd('MODE,1,TSB')
    dev.cmd('TABLE,CLEAR,1')
    # dev.cmd('TABLE,EDGE,1,RISING')
    dev.cmd('TABLE,APPEND,1,200.0,29.1,0,1')
    dev.cmd('TABLE,ARM,1')
    dev.cmd('TABLE,START,1')


dev.cmd('ON,1, ALL')
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