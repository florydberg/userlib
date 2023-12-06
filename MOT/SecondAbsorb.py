from labscript import start, stop
from generate_samples import generate_digital_samples, generate_analog_samples, test_word
from labscript_utils import import_or_reload
import_or_reload('labscriptlib.MOT.connection_table')

from labscriptlib.MOT.connection_table import *
from user_devices.mogdevice import MOGDevice
import json

from pypylon import pylon
import pylablib as pll
pll.par["devices/dlls/basler_pylon"] = "path/to/dlls"
from pylablib.devices import Basler

if True: # Time Constants
    t=0
    dt=board0.time_step # 1 us
    usec=dt
    us=usec
    msec=1000*dt
    ms=msec
    sec=1000000*dt
    s=sec
    min=60*sec

# PARAMETERS
Beam_ImgDuration= 2*usec
ImgDuration=50*usec
Basler_cameradelay=150*msec
twoD_delay=10*ms
TOF=50*usec
MOT_load=150*msec # time it takes for the atoms to load into the MOT

file_name=r'C:\Users\florydberg01\labscript-suite\userlib\labscriptlib\MOT\PARAMETERS'
file = open(file_name, 'w+')
data = {'TOF':TOF, 'ImgDuration':ImgDuration, 'MOT_load':MOT_load, 'twoD_delay': twoD_delay }
json.dump(data, file)

def take_image_andor(time):
    tt=time
    ANDOR.constant(tt, 5)
    tt+=ImgDuration
    ANDOR.constant(tt, 0)
    tt+=dt
    return tt 
    
def take_image_basler(time): # trigger pulse
    tt=time
    Basler_trg.go_high(tt) # trigger on
    tt+=ImgDuration # time of imaging duration
    Basler_trg.go_low(tt) # trigger off 
    tt+=dt
    return tt 

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

if False:
    camera.TriggerSelector.SetValue("FrameBurstStart")
    camera.TriggerSource.SetValue("Line3")
    camera.TriggerMode.SetValue("Off")
    camera.TriggerSelector.SetValue("FrameStart")
    camera.TriggerSource.SetValue("Line3")
    camera.TriggerMode.SetValue("Off")


for i in range(0,9):
    
    #---------Turn components on----------------
    COILS_switch.go_high(t) # Coils
    dueD_MOT_gate.go_high(t) # 2D MOT
    treD_MOT_gate.go_high(t) # 3D MOT
    #-------------------------------------------

    t+=MOT_load

   # Tweezer_gate.go_high(t)


    #---------Turn components off---------------
    dueD_MOT_gate.go_low(t) # 2D
    t+=twoD_delay # need delay for the 2D MOT to turn off
    treD_MOT_gate.go_low(t) # 3D
    COILS_switch.go_low(t) # Coils
    t+=dt # set t to the original time for next operation or sequence
    #-------------------------------------------

    # Basler_trg.go_high(t) # start acquiring
    # t+=dt
    # Basler_trg.go_low(t)

    t+=TOF # wait for time of flight

    #---------Image of the MOT--------------
    ImagingBeam_gate.go_high(t+5*usec) # turns on the imaging beam after t+x*usec. Q: Why 5usec? Because I want to be sure to illuminate the MOT while camera is already acquiring   
    take_image_basler(t-100*usec) # <----------------Imaging(Absorption): 100*usec is the delay in camera triggering
    t+=Beam_ImgDuration # Duration of image? AOM stays on for this duration
    ImagingBeam_gate.go_low(t+5*usec) # this goes low and also closes out image?
    #-----------------------------------------

    t+=1*Basler_cameradelay # wait for the camera to acquire image before next exposure

    #Tweezer_gate.go_high(t)

    #---------Image without the MOT---------
    ImagingBeam_gate.go_high(t+5*usec)
    take_image_basler(t-100*usec) #<---------------Imaging(Imaging_beam)
    t+=Beam_ImgDuration
    ImagingBeam_gate.go_low(t+5*usec)
    #----------------------------------------

    t+=1*Basler_cameradelay

    take_image_basler(t) #<---------------Imaging(ImagingBKG)
    t+=1*Basler_cameradelay # do not remove this otherwise you'll see MOT Light

    t+=dt




t+=100*msec 

# dueD_MOT_gate.go_high(t)#2D
# treD_MOT_gate.go_high(t)#3D
# ImagingBeam_gate.go_high(t)#3D


stop(t)
