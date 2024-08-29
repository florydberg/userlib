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
t=set_CompCoils(t)

#This code runs for 5 minutes the steady state blue mot. It can be used to check the mot status

live_time=60*s

for i in range(0,GLOBALS['n_loop']):

    COILScomp_SwitchON_TTL(t, True)
    set_CompCoils(t+5*us)    

    # t+=dt
    # BlueImaging_AOM_TTL(t, True)
    # t+=dt

    t=BlueMot_load(t, live_time)
    # t+=dt
    # BlueImaging_AOM_TTL(t, False)
    # t+=dt
    MOT_Blue2D_AOM_TTL(t-GLOBALS['TwoD_DELAY']+dt, False)
    MOT_Blue3D_AOM_TTL(t, False)
    t+=dt
    MOT_Blue3D_Shutter_TTL(t-1*msec, True)
    t+=dt
    COILSmain_Voltage(t, 0)
    t+=dt
    COILSmain_Current(t,0)
    t+=2*usec
    COILSmain_SwitchON_TTL(t, False)
    t+=dt



stop(t)