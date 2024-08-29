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

#This code is divided in three parts: blue mot loading, switch to multi frequency red mot (BBR), hold the mot and load the atoms in the tweezers.
#Fluorescence imaging is performed with the Andor camera

for i in range(0,GLOBALS['n_loop']):

    COILScomp_SwitchON_TTL(t, True)
    set_CompCoils(t+5*us)    

    #Options for this sequence
    shieldMulti = True
    resonantImaging = False
    in_tweezerImaging = True
    exposure_time=1000*usec

    #Beginning of the code

    MOT_Red3D_Switch_TTL(t, True)      #Global rf switch
    t+=dt  
    
    
    if shieldMulti:
        MOT_Red3D_AOM_TTL(t, False)     #Enables the single frequency red mot from the QRF
        t+=dt
        MOT_Red3D_multiFrq_TTL(t, True) 
        MOT_Red3D_singleFrq_TTL(t, False) 

    #Blue mot section
    t+=350*ms
    t=BlueMot_load(t, GLOBALS['loadTime_BlueMOT'])


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

    #Red mot section. Multifrequency goes on and the magnetic field gradient is set to the coils_current_ctrl_red value

    MOT_Red3D_AOM_TTL(t, False)        
    t+=dt
    MOT_Red3D_singleFrq_TTL(t, False) 
    t+=dt
    MOT_Red3D_multiFrq_TTL(t, True)

    t+=300*usec
    COILSmain_SwitchON_TTL(t, True)
    t+=dt
    COILSmain_Voltage(t, 0.4)
    t+=dt
    COILSmain_Current(t, GLOBALS['coils_current_ctrl_red'])          

    t+=GLOBALS['MOT_RED_duration']

    #Single frequency
    t+=dt

    MOT_Red3D_multiFrq_TTL(t, False)
    t+=dt
    MOT_Red3D_AOM_TTL(t, True)        #Single frequency mot
    t+=dt
    MOT_Red3D_singleFrq_TTL(t, True)     
    t+=GLOBALS['MOT_RED_duration']/4


    #Tweezers loading

    Twizzi_Switch_TTL(t, True)
    t+=GLOBALS['Tweezer_duration']/2

    MOT_Red3D_multiFrq_TTL(t, False)
    t+=dt
    COILSmain_Current(t, 0)
    t+=1*usec
    COILSmain_SwitchON_TTL(t, False)
    t+=dt
    MOT_Red3D_Switch_TTL(t, False)       
    t+=300*us
    # t+=GLOBALS['Tweezer_duration']/2

    #Imaging section. Choose within imaging with resonant light (tweezers are turned off) or in-trap imaging

    if resonantImaging:
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
   
    if in_tweezerImaging:
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

    

    COILScomp_SwitchON_TTL(t, False)

    setoff_CompCoils(t)
    t+=10*us

stop(t)