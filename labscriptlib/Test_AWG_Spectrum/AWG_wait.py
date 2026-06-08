#___________________________________________________________________________________#
from labscript import start, stop #                                                 |
from labscript_utils import import_or_reload #                                      |
import_or_reload('labscriptlib.Test_AWG_Spectrum.SUB_ROUTINES') #                   |
from labscriptlib.Test_AWG_Spectrum.SUB_ROUTINES import  msec, GLOBALS #  
from labscriptlib.Test_AWG_Spectrum.SUB_ROUTINES import *
#\______________________________ GENERAL LIBRARIES ________________________________/#

n_steps=GLOBALS['n_steps']
linear_ramp = GLOBALS['linear_ramp_moving']
grid=GLOBALS['grid_size']
n_loop=1e6


start()
t=0
t+=5*msec
t=all_moves_loading(t)
t+=dt

dio_2.go_high(t)

t+=5*msec

dio_2.go_low(t)


## REORDERING SEQUENCE

awg_trigger.go_high(t)
t+=1000*msec
awg_trigger.go_low(t)


t+=1*sec


# t+=movingTweezer(t,  0, 1, linear_ramp)

# start_reordering_sequence(t)

## REORDERING END

dio_2.go_high(t)

t+=1000*msec

dio_2.go_low(t)

stop(t+1500*msec)