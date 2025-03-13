from labscript import start, stop
from labscript_utils import import_or_reload
import_or_reload('labscriptlib.Sr.connection_table')

from tifffile import imsave

from labscriptlib.Sr.connection_table import *

if True: # Time Constants
    t=0
    dt=main_board.time_step # 1 us
    usec=dt
    us=usec
    msec=1000*dt
    ms=msec
    sec=1000000*dt
    s=sec
    min=60*sec

# PARAMETERS
Beam_ImgDuration= 5*usec
ImgDuration=50*usec
Basler_cameradelay=150*msec
twoD_delay=10*ms
TOF=100*usec
MOT_load=150*msec # time it takes for the atoms to load into the MOT
TweezDuration=50*msec

def take_image_basler(time): # trigger pulse
    tt=time
    CameraBasler_trg.go_high(tt) # trigger on
    tt+=Basler_Camera.trigger_duration
    CameraBasler_trg.go_low(tt) # trigger off 
    tt+=ImgDuration # time of imaging duration
    tt+=dt
    return tt 

start()

for i in range(0,n_loop):

    t+=Basler_Camera.expose(t,'Atoms', frametype='tiff')
    t+=1*sec

    t+=Basler_Camera.expose(t,'Probe', frametype='tiff')
    t+=1*sec 

    t+=Basler_Camera.expose(t,'Background', frametype='tiff')
    
    t+=1*sec 

stop(t)
