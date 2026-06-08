#___________________________________________________________________________________#
from labscript import start, stop #                                                 |
from labscript_utils import import_or_reload #                                      |
import_or_reload('labscriptlib.Test_AWG_Spectrum.SUB_ROUTINES') #                   |
from labscriptlib.Test_AWG_Spectrum.SUB_ROUTINES import  msec, dt, start_reordering_sequence, grid_size, GLOBALS #  
from labscriptlib.Test_AWG_Spectrum.SUB_ROUTINES import *
# import SUB_ROUTINES
#\______________________________ GENERAL LIBRARIES ________________________________/#

n_steps = GLOBALS['n_steps']
grid_size = GLOBALS['n_steps']

start()
t=0
start_reordering_sequence(t)

# t+=standingTweezer(t, range(0,25), amplitude=100, duration = 10)*150000

for jj in range(0,2):
    for ii in range(0,grid_size):
        t+=AllTheWay(t, ii*grid_size, 'horizontal')
        t+=50*usec

    for ii in range(0,grid_size):
        t+=AllTheWay(t, ii+grid_size, 'vertical')
        t+=50*usec

stop(t)