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

#PARAMETERS
ImgDuration=50*usec
cameradelay=30*msec

twoD_delay=10*ms

TOF=0*usec
TweezDuration=50*msec
current=6.5 #Amp

MOT_TIME=150*msec

import json
file_name=r'C:\Users\florydberg01\labscript-suite\userlib\labscriptlib\MOT\PARAMETERS'
file = open(file_name, 'w+')
data = {'current':current, 'TOF':TOF, 'ImgDuration':ImgDuration, 'MOT_TIME':MOT_TIME, 'twoD_delay': twoD_delay }
json.dump(data, file)

def take_image(time):############################
    tt=time
    ANDOR.constant(tt, 5)
    tt+=ImgDuration
    ANDOR.constant(tt, 0)
    tt+=dt
    return tt ###################################

start()
if True: # Connect to device
    dev = MOGDevice('192.168.1.102')
    print('Device info:', dev.ask('info'))
    dev.cmd(f'MODE,{1},NSB') 
    dev.cmd('ON,%i,ALL' % (1))  
    dev.cmd(f'MODE,{2},NSB') 
    dev.cmd('ON,%i,ALL' % (2))  
    dev.cmd(f'MODE,{4},NSB') 
    dev.cmd('ON,%i,ALL' % (4))  

for i in range(0,1):

    t+=dt
    COILS_switch.go_high(t)#Coils

    dueD_MOT_gate.go_high(t)#2D
    treD_MOT_gate.go_high(t)#3D

    t+=MOT_TIME

    Tweezer_gate.go_high(t)
    t+=TweezDuration

    dueD_MOT_gate.go_low(t)#2D
    t+=twoD_delay
    treD_MOT_gate.go_low(t)#3D

    COILS_switch.go_low(t)#Coils
    
    t+=50*msec 
    Tweezer_gate.go_low(t)

    t+=TOF

    ImagingBeam_gate.go_high(t)
    ImagingBeam_gate.go_low(t+5*usec)
    t=take_image(time=t+dt)
    
    i+=1

t+=1*msec 
dueD_MOT_gate.go_high(t)#2D
treD_MOT_gate.go_high(t)#3D

stop(t)
