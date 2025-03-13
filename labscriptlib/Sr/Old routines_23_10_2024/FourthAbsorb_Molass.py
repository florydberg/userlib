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

    t=BlueMOT_molass(t, GLOBALS['loadTime_BlueMOT'], GLOBALS['T_BlueMolass'])

    t+=GLOBALS['TOF']

    t=take_absorbImaging(t, GLOBALS['AbsImgPulse_duration'])
    t+=dt
    treD_MOT_gate.go_high(t)

stop(t+dt)