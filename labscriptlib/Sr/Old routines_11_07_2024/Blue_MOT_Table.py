#___________________________________________________________________________________#
from labscript import start, stop #                                                 |
from labscript_utils import import_or_reload #                                      |
import_or_reload('labscriptlib.Sr.SUB_ROUTINES') #                                  |
from labscriptlib.Sr.SUB_ROUTINES import * #                                        |
#\______________________________ GENERAL LIBRARIES ________________________________/#

start()
t+=dt
set_MOGLABS_ready(t)
COILScomp_SwitchON_TTL(t, True)
set_CompCoils(t+5*us)      
TABLE_MODE_ON('treD_MOT', t)

for i in range(0,GLOBALS['n_loop']):

    t=BlueMot_Table(t, GLOBALS['loadTime_BlueMOT'])

    t+=GLOBALS['TOF'] # wait for time of flight

    t=take_absorbImaging(t, GLOBALS['AbsImgPulse_duration'])

    t+=dt

COILScomp_SwitchON_TTL(t, False)

setoff_CompCoils(t)
t+=10*us
stop(t+dt)