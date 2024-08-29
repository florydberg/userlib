#example

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

Beam_ImgDuration= 2*usec
ImgDuration=5*msec
Basler_cameradelay=150*msec

start()
t=0
for i in range(0,9):

    Basler_trg.go_high(t) # trigger on
    t+=ImgDuration # time of imaging duration
    Basler_trg.go_low(t) # trigger off 
    print(i)

    t+=1*Basler_cameradelay

    Basler_trg.go_high(t) # trigger on
    t+=ImgDuration # time of imaging duration
    Basler_trg.go_low(t) # trigger off 
    print(i)

    t+=1*Basler_cameradelay

    Basler_trg.go_high(t) # trigger on
    t+=ImgDuration # time of imaging duration
    Basler_trg.go_low(t) # trigger off 
    print(i)

stop(t)




