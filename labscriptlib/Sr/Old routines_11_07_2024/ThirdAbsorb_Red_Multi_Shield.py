#___________________________________________________________________________________#
from labscript import start, stop #                                                 |
from labscript_utils import import_or_reload #                                      |
import_or_reload('labscriptlib.Sr.SUB_ROUTINES') #                                  |
from labscriptlib.Sr.SUB_ROUTINES import * #                                        |
#\______________________________ GENERAL LIBRARIES ________________________________/#

start()
t+=dt
set_MOGLABS_ready(t)


for i in range(0,GLOBALS['n_loop']):

    t=BlueMot(t, GLOBALS['loadTime_BlueMOT'])

    RedMot_multifrq(t-GLOBALS['loadTime_BlueMOT'], GLOBALS['loadTime_BlueMOT'])

    t+=GLOBALS['TOF'] # wait for time of flight
    
    t=take_absorbImaging(t, GLOBALS['AbsImgPulse_duration'])
    # t+=2*sec

t+=0.1*sec
stop(t) 