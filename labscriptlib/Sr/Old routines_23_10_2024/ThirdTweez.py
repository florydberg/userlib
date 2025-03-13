#___________________________________________________________________________________#
from labscript import start, stop #                                                 |
from labscript_utils import import_or_reload #                                      |
import_or_reload('labscriptlib.Sr.SUB_ROUTINES') #                                  |
from labscriptlib.Sr.SUB_ROUTINES import * #                                        |
#\______________________________ GENERAL LIBRARIES ________________________________/#

start()
t+=dt
# set_MOGLABS_ready(t)

duration= 1e-5 #in sec duation of sample as step
# Vertical.generate_multiple_tones(1e-6,4*4096/1.25e9,[100e6, 90e6, 110e6])

for i in range(0,GLOBALS['n_loop']):

    t+=+100*msec
    awg_trigger.go_high(t)

    t+=+10*sec
    awg_trigger.go_low(t)

stop(t+1*sec) #to cool coils down
