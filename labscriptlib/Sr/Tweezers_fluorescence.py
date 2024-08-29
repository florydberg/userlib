# originates from Absorption_BlueRed_MOT.py
#___________________________________________________________________________________#
from labscript import start, stop #                                                 |
from labscript_utils import import_or_reload #                                      |
import_or_reload('labscriptlib.Sr.SUB_ROUTINES') #                                  |
from labscriptlib.Sr.SUB_ROUTINES import * #                                        |
#\______________________________ GENERAL LIBRARIES ________________________________/#

shield = False
shieldMulti = True

sel_mot_blue = True
sel_mot_red = True
sel_mot_red_sf = True
sel_tweezer = True

sel_fluo_image = True
sel_abs_image = False

sel_imaging_beam = "abs"
# sel_imaging_beam = 'tweez'
# sel_imaging_beam = '3Dmot'

# sel_camera_fluo = 'andor'
sel_camera_fluo ='orca'
# sel_camera_fluo = 'basler_abs'
# sel_camera_fluo = 'basler_fluo'

# sel_camera_abs = 'andor'
sel_camera_abs = 'basler_abs'
#sel_camera_abs = 'basler_fluo'

sel_table_red=True

start()
TABLE_MODE_ON('RedMOT', t)
t+=dt
set_MOGLABS_ready(t)
t+=dt
t=set_CompCoils(t)
exposure_time=10000*usec
t+=500*msec


for i in range(0,GLOBALS['n_loop']):

    COILScomp_SwitchON_TTL(t, True)
    set_CompCoils(t+5*us)    

    MOT_Red3D_Switch_TTL(t, True)      #Global rf switch
    t+=dt

    if shield:
        MOT_Red3D_AOM_TTL(t, True)     
        t+=dt
        MOT_Red3D_multiFrq_TTL(t, False) 
        MOT_Red3D_singleFrq_TTL(t, True) 

    if shieldMulti:
        MOT_Red3D_AOM_TTL(t, False)     
        t+=dt
        MOT_Red3D_multiFrq_TTL(t, True) 
        MOT_Red3D_singleFrq_TTL(t, False) 

    ##### BLUE MOT #################
    if sel_mot_blue:
        print("Blue MOT")
    
    t=BlueMot_load(t, GLOBALS['loadTime_BlueMOT'])

    MOT_Blue2D_AOM_TTL(t-GLOBALS['TwoD_DELAY']+dt, False)
    MOT_Blue3D_AOM_TTL(t, False)
    t+=dt
    MOT_Blue3D_Shutter_TTL(t-1*msec, True)

    # treD_MOT.DDS.setamp(tt, GLOBALS['treD_MOT_Pow']*1e2/10)

    t+=dt
    COILSmain_Voltage(t, 0)
    t+=dt
    COILSmain_Current(t,0)
    t+=1*usec
    COILSmain_SwitchON_TTL(t, False)
    t+=dt

    if sel_mot_red:
        ##### MULTI RED MOT #################
        MOT_Red3D_AOM_TTL(t, False)        #Luca moved this part here to turn on the comb even during the switching off
        t+=dt
        MOT_Red3D_singleFrq_TTL(t, False) 
        t+=dt
        MOT_Red3D_multiFrq_TTL(t, True)

        ##########
        t+=300*usec 
        COILSmain_SwitchON_TTL(t, True)
        t+=dt
        COILSmain_Voltage(t, 0.4)
        t+=dt 
        COILSmain_Current(t, GLOBALS['coils_current_ctrl_red'])          #Turn on the COILSmain at 10 A, roughly 5 G/cm
        ###########

        t+=GLOBALS['MOT_RED_duration']
        MOT_Red3D_multiFrq_TTL(t, False)
        t+=dt

        if sel_mot_red_sf:
            ##### SINGLE RED MOT #################    
            if sel_table_red:
                NEW_TABLE_LINE('RedMOT', t, GLOBALS['Red_MOT_Frq']/1e6, GLOBALS['Red_MOT_Pow'])
            else:
                MOT_Red3D_AOM_TTL(t, True)     
            t+=3*dt
            MOT_Red3D_singleFrq_TTL(t, True)     
            t+=GLOBALS['MOT_RED_SF_duration']
            MOT_Red3D_Switch_TTL(t, False)       
            MOT_Red3D_singleFrq_TTL(t, False)
            t+=dt

        #### RED MOT Turn Off
        COILSmain_Current(t, 0)
        t+=1*usec
        COILSmain_SwitchON_TTL(t, False)
        t+=dt

        if sel_tweezer:
            ##### Tweezers loading #################
            t-=GLOBALS['Tweezer_duration']
            Twizzi_Switch_TTL(t, True)
            t+=GLOBALS['Tweezer_duration']
            # Sisyphus_AOM_TTL(t,True)
            #COILScomp_SwitchON_TTL(t, False)
            # setoff_CompCoils(t)
            # t+=10*ms     #"TOF"
            # Sisyphus_AOM_TTL(t,False)
            t+=GLOBALS['FluoImgPulse_duration'] # tweezer stays on during fluo imaging
            t+=dt
            Twizzi_Switch_TTL(t, False)
            t+=dt
    ##### ALL OFF #################

    if sel_fluo_image:
        t_ahead_fluoimag = GLOBALS['FluoImgPulse_duration'] # matches RedMot single freq duration
        #t_ahead_fluoimag = GLOBALS['MOT_RED_duration']+100*msec # to see Blue MOT

        t-=t_ahead_fluoimag ########### TIME MACHINE  ############################ for Fluorescence
        #Andor camera needs 20 ms to clean sensor from previously collected light
        if sel_imaging_beam=="abs":
            BlueImaging_AOM_TTL(t,True)
            BlueImaging_AOM_TTL(t+GLOBALS['FluoImgPulse_duration']+dt, False)
        elif sel_imaging_beam=='tweez':
            BlueImagingTweez_AOM_TTL(t, True)
            BlueImagingTweez_AOM_TTL(t+GLOBALS['FluoImgPulse_duration']+dt, False)
        elif sel_imaging_beam=='3Dmot':
            MOT_Blue3D_AOM_TTL(t, True)
            MOT_Blue3D_AOM_TTL(t+GLOBALS['FluoImgPulse_duration']+dt, False)
        
        if sel_camera_fluo=='andor':
            Andor_Camera_fluo_readout=(1024*1024/1e6*sec+1024*2.2*usec)+100*msec # Horizontal readout + vertical shift times + buffer
            t+=100*us
            Andor_Camera_trigger.go_high(t)
            Andor_Camera_trigger.go_low(t+1*msec)
            # Andor camera is controlled by Andor Solis
            # t+=1024*2.2*usec+GLOBALS['FluoImgPulse_duration']+10*msec
            # t+=Andor_Camera_fluo_readout+200*ms
            # Andor_Camera_trigger.go_high(t)
            # Andor_Camera_trigger.go_low(t+1*msec)
            t+=dt
            t=take_absorbImaging(t, GLOBALS['AbsImgPulse_duration'])
            # Basler_Camera_fluo_trigger.go_high(t-100*usec-5*usec)           #Test to use both the cameras for the fluorescence
            # Basler_Camera_fluo_trigger.go_low(t+1*msec)
            t+=Andor_Camera_fluo_readout
        elif sel_camera_fluo=='orca':
            trigger_delay=200*usec
            Andor_Camera_fluo_readout=(1024*1024/1e6*sec+1024*2.2*usec)+100*msec # Horizontal readout + vertical shift times + buffer
            t+=100*us
            Andor_Camera_trigger.go_high(t-trigger_delay)
            Andor_Camera_trigger.go_low(t-trigger_delay+1*msec)
            # Andor camera is controlled by Andor Solis
            # t+=1024*2.2*usec+GLOBALS['FluoImgPulse_duration']+10*msec
            # t+=Andor_Camera_fluo_readout+200*ms
            # Andor_Camera_trigger.go_high(t)
            # Andor_Camera_trigger.go_low(t+1*msec)
            t+=dt
            t=take_absorbImaging(t, GLOBALS['AbsImgPulse_duration'])
            # Basler_Camera_fluo_trigger.go_high(t-100*usec-5*usec)           #Test to use both the cameras for the fluorescence
            # Basler_Camera_fluo_trigger.go_low(t+1*msec)
            t+=Andor_Camera_fluo_readout
        elif sel_camera_fluo=='basler_abs':
            Basler_Camera_abs_trigger.go_high(t-100*usec-5*usec)
            Basler_Camera_abs_trigger.go_low(t+1*msec)
            Basler_Camera_abs.expose(t-100*usec+5*usec,'Fluo', frametype='tiff')
        elif sel_camera_fluo=='basler_fluo':
            Basler_Camera_fluo_trigger.go_high(t-100*usec-5*usec)
            Basler_Camera_fluo_trigger.go_low(t+1*msec)
            # Basler camera for fluorescence is controlled by Pylon Viewer
            #Basler_Camera_fluo.expose(t-100*usec+5*usec,'Fluo', frametype='tiff')
        t+=t_ahead_fluoimag ############### TIME MACHINE  ############################

    t+=GLOBALS['TOF']# wait for time of flight
    
    if sel_abs_image:
        if sel_camera_abs=='andor':
            trigger_delay=20*usec #100 for camera activation + 5 as safety buffer
            Andor_Camera_abs_readout=(1024*1024/30e6*sec+1024*2.2*usec)+30*msec # Horizontal readout + vertical shift times + buffer
            beam_duration = 500*usec

            Andor_Camera_trigger.go_high(t-trigger_delay)
            Andor_Camera_trigger.go_low(t-trigger_delay+100*usec)
            t+=dt
            Basler_Camera_fluo_trigger.go_high(t-100*usec-5*usec)
            Basler_Camera_fluo_trigger.go_low(t+1*msec)
            t+=dt
            BlueImagingTweez_AOM_TTL(t, True)
            BlueImagingTweez_AOM_TTL(t+beam_duration, False)
            t+=beam_duration+Andor_Camera_abs_readout
            Andor_Camera_trigger.go_high(t-trigger_delay)
            Andor_Camera_trigger.go_low(t-trigger_delay+100*usec)
            BlueImagingTweez_AOM_TTL(t, True)
            BlueImagingTweez_AOM_TTL(t+beam_duration, False)
            t+=beam_duration+Andor_Camera_abs_readout
            Andor_Camera_trigger.go_high(t-trigger_delay)
            Andor_Camera_trigger.go_low(t-trigger_delay+100*usec)
            t+=beam_duration+Andor_Camera_abs_readout
        elif sel_camera_abs =='basler_abs':
            t=take_absorbImaging(t, GLOBALS['AbsImgPulse_duration'])

    t+=500*us
    Twizzi_Switch_TTL(t, False)
    t+=dt
    COILScomp_SwitchON_TTL(t, False)
    setoff_CompCoils(t)
    t+=10*us

stop(t+100*ms)