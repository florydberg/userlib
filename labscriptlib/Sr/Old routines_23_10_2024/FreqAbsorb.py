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
ImgDuration=400*usec
cameradelay=25*msec

def take_image(time):############################
    tt=time
    ANDOR.constant(tt, 5)
    tt+=ImgDuration
    ANDOR.constant(tt, 0)
    tt+=dt
    return tt ###################################

start()
if False: # Connect to device
    dev = MOGDevice('192.168.1.102')
    print('Device info:', dev.ask('info'))

for i in range(0,10):

    dev.cmd('TABLE,APPEND,3,111,30.0,0,1')
    COILS.constant(t, 3.1)
    t+=dt

    dueD_MOT_gate.go_high(t)
    treD_MOT_gate.go_high(t)

    t+=dt

    t+=2*sec

    t+=10*msec 

    t=take_image(time=t)#<-----------------Imaging(MOT)
    t+=cameradelay

    dueD_MOT_gate.go_low(t)
    treD_MOT_gate.go_low(t)


    t+=1*usec

    ImagingBeam_gate.go_high(t+10*usec)
    t=take_image(time=t)#<----------------Imaging(Absorbition)
    ImagingBeam_gate.go_low(t)

    t+=dt
    COILS.constant(t, 0)

    t+=cameradelay

    ImagingBeam_gate.go_high(t+10*usec)
    t=take_image(time=t)#<---------------Imaging(Imaging_beam)
    ImagingBeam_gate.go_low(t)

    t+=cameradelay

    t=take_image(time=t)#<---------------Imaging(BKG)

    t+=1*msec
    i+=1

stop(t)
