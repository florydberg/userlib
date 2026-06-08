#___________________________________________________________________________________#
from labscript import start, stop #                                                 |
from labscript_utils import import_or_reload #                                      |
import_or_reload('labscriptlib.Sr.SUB_ROUTINES') #                   |
from labscriptlib.Sr.SUB_ROUTINES import  msec, dt, GLOBALS #  
from labscriptlib.Sr.SUB_ROUTINES import *
# import SUB_ROUTINES
#\______________________________ GENERAL LIBRARIES ________________________________/#


grid_size = 3


start()
t=0


t+=standingTweezer(t, range(0,grid_size**2), amplitude=100, duration = 10)*150000
awg_trigger.go_high(t) # Trigger the AWG to start the sequence

# Basler_Camera_extra_trigger.go_high(t)

for jj in range(0,1):
    for ii in range(0,grid_size):
        t+=AllTheWay(t, ii*grid_size, 'horizontal')
        t+=500*usec

    for ii in range(0,grid_size):
        t+=AllTheWay(t, ii+grid_size, 'vertical')
        t+=500*usec

stop(t+10*sec)