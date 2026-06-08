#___________________________________________________________________________________#
from labscript import start, stop #                                                 |
from labscript_utils import import_or_reload #                                      |
import_or_reload('labscriptlib.Sr.SUB_ROUTINES') #                   |
from labscriptlib.Sr.SUB_ROUTINES import  msec, GLOBALS #  
from labscriptlib.Sr.SUB_ROUTINES import *
#\______________________________ GENERAL LIBRARIES ________________________________/#

linear_ramp = GLOBALS['linear_ramp_moving']
grid=GLOBALS['grid_size']
n_loop=1e6


start()
t=0
t+=5*msec
# t=all_moves_loading(t)
t+=dt


## REORDERING SEQUENCE

awg_trigger.go_high(t)
t+=1000*msec
awg_trigger.go_low(t)


t+=1*sec


# t+=movingTweezer(t,  0, 1, linear_ramp)

# start_reordering_sequence(t)



stop(t+1500*msec)