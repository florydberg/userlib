from labscript import start, stop
from generate_samples import generate_digital_samples, generate_analog_samples, test_word
from labscript_utils import import_or_reload
import_or_reload('labscriptlib.example_apparatus.connection_table')

from labscriptlib.example_apparatus.connection_table import *
from user_devices.mogdevice import MOGDevice

# t = board0.start_time
t=0
dt=board0.time_step #1mu second
usec=dt
msec=1000*dt
sec=1000000*dt

def take_image(time):############
    tt=time
    tt+=20*msec
    # Andor_trg.go_high(tt)     #
    ANDOR.constant(tt, 5)
    tt+=100*msec#---Exposure Time
    ANDOR.constant(tt, 0)
    # Andor_trg.go_low(tt)      #
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
    dev.cmd('MODE,2,TSB')
    dev.cmd('TABLE,CLEAR,2')
    dev.cmd('MODE,3,TSB')
    dev.cmd('TABLE,CLEAR,3')
    dev.cmd('MODE,4,TSB')
    dev.cmd('TABLE,CLEAR,3')

    # dev.cmd('TABLE,EDGE,1,RISING')
    dev.cmd('TABLE,APPEND,1,200.0,29.1,0,1')
    dev.cmd('TABLE,APPEND,2,180.0,29.1,0,1')
    dev.cmd('TABLE,APPEND,3,114.0,30.0,0,1')
    dev.cmd('TABLE,APPEND,4,218.0,29.1,0,1')
    
    # dev.cmd('TABLE,ARM,1')

    dev.cmd('TABLE,START,1')
    dev.cmd('TABLE,START,2')
    dev.cmd('TABLE,START,3')
    dev.cmd('TABLE,START,4')



stop(t)
