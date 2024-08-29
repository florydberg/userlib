from labscript import start, stop
from generate_samples import generate_digital_samples, generate_analog_samples, test_word
from labscript_utils import import_or_reload
import_or_reload('labscriptlib.MOT.connection_table')

from labscriptlib.MOT.connection_table import *
from user_devices.mogdevice import MOGDevice

t=0
dt=board0.time_step #1mu second
usec=dt
msec=1000*dt
sec=1000000*dt
s=sec
Exposure=100*usec

def take_image(time):############################
    tt=time
    ANDOR.constant(tt, 5)
    tt+=Exposure
    ANDOR.constant(tt, 0)
    tt+=dt
    return tt ###################################

start()
if False: # Connect to device
    dev = MOGDevice('192.168.1.102')
    print('Device info:', dev.ask('info'))

time=10000*dt
while t<time:
    ImagingBeam_gate.go_high(t)
    t+=10*dt
    ImagingBeam_gate.go_low(t)



stop(t)
