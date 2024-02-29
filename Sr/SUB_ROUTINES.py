#SUB ROUTINES
from labscript_utils import import_or_reload
import_or_reload('labscriptlib.Sr.connection_table')
from labscriptlib.Sr.connection_table import *
from user_devices.mogdevice import MOGDevice

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

if True: # PARAMETERS
    Basler_cameradelay=150*msec #TODO:  change into fixed by device
    twoD_delay=10*ms
    loadingMOT_time=150*msec # time it takes for the atoms to load into the MOT

def BlueMot_on(tt,loadingMOT_time):
    COILS_switch.go_high(tt) # Coils
    dueD_MOT_gate.go_high(tt) # 2D MOT
    treD_MOT_gate.go_high(tt) # 3D MOT
    tt+=loadingMOT_time
    return tt

def BlueMot_off(tt,twoD_delay):
    dueD_MOT_gate.go_low(tt) # 2D
    tt+=twoD_delay # need delay for the 2D MOT to turn off
    treD_MOT_gate.go_low(tt) # 3D
    COILS_switch.go_low(tt) # Coils
    return tt

def BlueMot(tt,duration_on,duration_off, duration_wait):
    tt+=BlueMot_on(tt, duration_on)
    tt+=BlueMot_off(tt+duration_wait, duration_off)
    return tt

def take_absorbImaging(tt, beam_duration):
    ImagingBeam_gate.go_high(tt+5*usec)
    tt+=Basler_Camera.expose(tt-100*usec,'Atoms', frametype='tiff')
    tt+=beam_duration 
    ImagingBeam_gate.go_low(tt+5*usec)

    tt+=1*sec # loading camera time

    ImagingBeam_gate.go_high(tt+5*usec)
    tt+=Basler_Camera.expose(tt-100*usec,'Probe', frametype='tiff')
    tt+=beam_duration 
    ImagingBeam_gate.go_low(tt+5*usec)

    tt+=1*sec # loading camera time

    Basler_Camera.expose(tt-100*usec,'Background', frametype='tiff')

    tt+=1*sec # loading camera time

    return tt

def BlueMogLabs_On(): # Connect to device
    dev = MOGDevice('192.168.1.102')
    print('Device info:', dev.ask('info'))
    dev.cmd(f'MODE,{1},NSB') 
    dev.cmd('ON,%i,ALL' % (1))  
    dev.cmd(f'MODE,{2},NSB') 
    dev.cmd('ON,%i,ALL' % (2)) 
    dev.cmd(f'MODE,{3},NSB') 
    dev.cmd('ON,%i,ALL' % (4))  
    dev.cmd(f'MODE,{4},NSB') 
    dev.cmd('ON,%i,ALL' % (4))  

def do_Tweezer(tt, Tweezer_duration):
    Tweezer_gate.go_high(tt)
    tt+Tweezer_duration
    Tweezer_gate.go_low(tt)
    return tt
    
def take_fluoImagig(tt):
    # ImagingBeam_gate.go_high(tt+10*usec)
    tt+=Andor_Camera.expose(tt, 'Tweezer', frametype='tiff') 
    # ImagingBeam_gate.go_low(tt)
    return tt
