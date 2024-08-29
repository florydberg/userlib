from labscript import start, stop
from generate_samples import generate_digital_samples, generate_analog_samples, test_word
from labscript_utils import import_or_reload
import_or_reload('labscriptlib.example_apparatus.connection_table')

from labscriptlib.example_apparatus.connection_table import *
from user_devices.mogdevice import MOGDevice

t=0
dt=board0.time_step #1mu second
usec=dt
msec=1000*dt
sec=1000000*dt


def take_image(time):###########
    tt=time
    # tt+=20*msec
    ANDOR.constant(tt, 5)
    tt+=100*usec
    ANDOR.constant(tt, 0)
    tt+=dt
    return tt###################

start()
if True:
    # Connect to device
    dev = MOGDevice('192.168.1.100')
    print('Device info:', dev.ask('info'))

    channel = 1  # channel 1-4
    frequency = 200.0  # frequency in MHz

    dev.cmd('OFF,1')
    t=+2*dt
    dev.cmd('MODE,1,TSB')
    dev.cmd('TABLE,CLEAR,1')
    dev.cmd('TABLE,EDGE,1,RISING')
    dev.cmd('TABLE,APPEND,1,200.0,29.1,0,1')
    dev.cmd('TABLE,ARM,1')
    dev.cmd('TABLE,START,1')
    dev.cmd('ON,1, ALL')
    # dev.cmd('ON,2, SIG')


ANDOR.constant(t, 0)

t+=0.1*sec

t=take_image(time=t)#<-------------Imaging(BKG)

t+=2.5*sec


Imaging.enable(t)
t+=10*usec
t=take_image(time=t)#<-------------Imaging(BEAM)
Imaging.disable(t)
t+=1.5*sec


dueD_MOT.enable(t)
treD_MOT.enable(t)
t+=dt
COILS.constant(t, 3.1)

t+=1*sec

COILS.constant(t, 0)
t+=dt
dueD_MOT.disable(t)
treD_MOT.disable(t)

t+=dt

Imaging.enable(t)
t+=10*usec
t=take_image(time=t)#<-------------Imaging(BEAM)
Imaging.disable(t)
t+=2*sec

stop(t)
