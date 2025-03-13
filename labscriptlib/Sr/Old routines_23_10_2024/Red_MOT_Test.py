#___________________________________________________________________________________#
from labscript import start, stop #                                                 |
from labscript_utils import import_or_reload #                                      |
import_or_reload('labscriptlib.Sr.SUB_ROUTINES') #                                  |
from labscriptlib.Sr.SUB_ROUTINES import * #                                        |
#\______________________________ GENERAL LIBRARIES ________________________________/#

start()
TABLE_MODE_ON('Free', t)
t+=dt
set_MOGLABS_ready(t)
t+=dt
# t=set_CompCoils(t)
exposure_time=10000*usec
# t+=500*msec

# COILScomp_SwitchON_TTL(t, True)
set_CompCoils(t+5*us)    

for i in range(0,GLOBALS['n_loop']):


    t=RedBroad_Mot_Test(t, GLOBALS['MOT_RED_duration'], GLOBALS['loadTime_BlueMOT'], shield=False, shieldMulti=True)     
    t+=dt

    t-=GLOBALS['MOT_RED_duration']/6   ########### TIME MACHINE  ############################ 600*msec for BlueMot

    delay=GLOBALS['delay']

    BlueImagingTweez_AOM_TTL(t, True)
    # MOT_Blue3D_AOM_TTL(t, True)

    Andor_Camera_trigger.go_high(t-delay)
    t+=dt
    Basler_Camera_fluo_trigger.go_high(t-delay-100*usec-5*usec)

    Andor_Camera_trigger.go_low(t+1*msec-delay)
    t+=dt
    Basler_Camera_fluo_trigger.go_low(t+1*msec-delay)

    # MOT_Blue3D_AOM_TTL(t+GLOBALS['FluoImgPulse_duration']+dt, False)
    BlueImagingTweez_AOM_TTL(t+GLOBALS['FluoImgPulse_duration']+dt, False)
    t+=dt

    t+=GLOBALS['MOT_RED_duration']/6 ############### TIME MACHINE  ############################



   
    t+=GLOBALS['TOF']# wait for time of flight

    NEW_TABLE_LINE('Free', t, 20, 29)

    t=take_absorbImaging(t, GLOBALS['AbsImgPulse_duration'])


    if False: #RESONANT
        Twizzi_Switch_TTL(t, False)
        t+=5*us
        BlueImaging_AOM_TTL(t+10*usec, True)

        t-=100*msec

        Andor_Camera_trigger.go_high(t)
        t+=Andor_Camera.expose(t+dt,'Fluo'+str(i), frametype='tiff') 
        t+=10*usec   
        Andor_Camera_trigger.go_low(t)

        t+=100*msec

        t+=exposure_time

        BlueImaging_AOM_TTL(t, False)
        t+=600*msec

    if False: #INTWEEZER
        t+=dt
        BlueImagingTweez_AOM_TTL(t+10*usec, True)

        t-=100*msec

        Andor_Camera_trigger.go_high(t)
        Andor_Camera.expose(t+dt, 'Fluo'+str(i), frametype='tiff') 
        t+=10*usec   
        Andor_Camera_trigger.go_low(t)

        t+=100*msec

        t+=exposure_time

        BlueImagingTweez_AOM_TTL(t, False)
        t+=dt 
        Twizzi_Switch_TTL(t, False)
        t+=600*msec

# COILScomp_SwitchON_TTL(t, False)
setoff_CompCoils(t)
t+=10*us
# t+=600*msec
TABLE_MODE_OFF('Free', t)

stop(t)
















































































































































































































stop(t)