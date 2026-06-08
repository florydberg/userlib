#___________________________________________________________________________________#
from labscript import start, stop #                                                 |
from labscript_utils import import_or_reload #                                      |
import_or_reload('labscriptlib.Test_AWG_Spectrum.SUB_ROUTINES') #                   |
from labscriptlib.Test_AWG_Spectrum.SUB_ROUTINES import  msec, dt, start_reordering_sequence, movingTweezer, GLOBALS #  
from labscriptlib.Test_AWG_Spectrum.SUB_ROUTINES import *
# import SUB_ROUTINES
#\______________________________ GENERAL LIBRARIES ________________________________/#

n_steps=GLOBALS['n_steps']
linear_ramp = GLOBALS['linear_ramp_moving']
grid=GLOBALS['grid_size']

start()
t=0
start_reordering_sequence(t)

central=round(grid_size*3/2)

n_loop=1e6



t+=standingTweezer(t, range(0,grid**2), amplitude=100, duration = 10)*n_loop

# t+=movingTweezer(t,  central-1, central, linear_ramp)*n_loop

# t+=movingTweezer(t,  central-1, central, linear_ramp)*n_loop
# t+=movingTweezer(t, central,central+grid_size, linear_ramp)*n_loop

# t+=movingTweezer(t, central+grid_size, central+1, linear_ramp)*n_loop

# t+=movingTweezer(t, central+1, central+grid_size+1, linear_ramp)*n_loop

# for ii in range(0,24):
#     t+=standingTweezer(t, ii, amplitude=10, duration = 10)*150000

# for ii in range(0,5):
#     t+=AllTheWay(t, ii*5, 'horizontal')*1500000
# for ii in range(0,5):
#     t+=AllTheWay(t, ii*5, 'vertical')*1500000

stop(t+1*msec)