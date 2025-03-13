#___________________________________________________________________________________#
from labscript import start, stop #                                                 |
from labscript_utils import import_or_reload #                                      |
import_or_reload('labscriptlib.Sr.SUB_ROUTINES') #                                  |
from labscriptlib.Sr.SUB_ROUTINES import * #                                        |
#\______________________________ GENERAL LIBRARIES ________________________________/#

start()
t+=dt
set_MOGLABS_ready(t)
t+=dt

for i in range(0,GLOBALS['n_loop']):

    t=RedBroad_Mot(t, GLOBALS['MOT_RED_duration'], GLOBALS['loadTime_BlueMOT'], shield=True)

    t+=GLOBALS['TOF'] # wait for time of flight
    
    t=take_absorbImaging(t, GLOBALS['AbsImgPulse_duration'])

stop(t)