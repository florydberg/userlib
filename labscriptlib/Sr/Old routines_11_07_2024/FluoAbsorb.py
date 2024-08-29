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

    set_CompCoils(t)      

    take_fluoImaging_Basler(t+GLOBALS['loadTime_BlueMOT']/1.5, 'fluo_MOT')
    t=BlueMot(t, GLOBALS['loadTime_BlueMOT'])
    
    setoff_CompCoils(t)

    t+=GLOBALS['TOF'] # wait for time of fligh

    t=take_absorbImaging(t, GLOBALS['AbsImgPulse_duration'])
    
stop(t+dt)