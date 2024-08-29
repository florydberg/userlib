#___________________________________________________________________________________#
from labscript import start, stop #                                                 |
from labscript_utils import import_or_reload #                                      |
import_or_reload('labscriptlib.Sr.SUB_ROUTINES') #                                  |
from labscriptlib.Sr.SUB_ROUTINES import * #    
#\______________________________ GENERAL LIBRARIES ________________________________/#

start()
t+=dt
# set_MOGLABS_ready(t)
G_MOT_RED = GLOBALS['MOT_RED']
# G_RedStart_delay = GLOBALS['RedStart_delay']
# G_RedStop_delay = GLOBALS['RedStop_delay']

for i in range(0,GLOBALS['n_loop']):

    if G_MOT_RED: t=RedMot_on(t+GLOBALS['RedStart_delay'])

    t=BlueMot(t, GLOBALS['loadTime_BlueMOT'], GLOBALS['MOT_duration'])

    if G_MOT_RED: t=RedMot_off(t+GLOBALS['RedStop_delay'])

    t+=GLOBALS['TOF'] # wait for time of flight

    t=take_absorbImaging(t, GLOBALS['AbsImgPulse_duration'])
    t+=5*sec

stop(t+1*sec) #to cool coils down
