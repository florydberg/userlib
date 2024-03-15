from labscript import start, stop #                                                 |
from labscript_utils import import_or_reload #                                      |
import_or_reload('labscriptlib.Sr.SUB_ROUTINES') #                                  |
from labscriptlib.Sr.SUB_ROUTINES import * #                                        |
#\______________________________ GENERIC LIBRARIES ________________________________/#

start()
t+=dt
# set_MOGLABS_ready(t)

for i in range(0,GLOBALS['n_loop']):

    t=BlueMot(t, GLOBALS['loadTime_BlueMOT'], GLOBALS['MOT_duration'])

    t+=GLOBALS['TOF'] # wait for time of fligh

    t=take_absorbImaging(t, GLOBALS['AbsImgPulse_duration'])
    t+=5*sec

stop(t+1*sec) #to cool coils down
