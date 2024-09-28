# originates from Absorption_BlueRed_MOT.py
#___________________________________________________________________________________#
from labscript import start, stop #                                                 |
from labscript_utils import import_or_reload #                                      |
import_or_reload('labscriptlib.Sr.SUB_ROUTINES') #                                  |
from labscriptlib.Sr.SUB_ROUTINES import * #                                        |
#\______________________________ GENERAL LIBRARIES ________________________________/#

if True: ## Selects ##
    shieldSingle = GLOBALS['shieldSingle']
    shieldMulti = GLOBALS['shieldMulti']

    sel_mot_blue = GLOBALS['mot_blue']
    sel_mot_red = GLOBALS['mot_red']
    sel_mot_red_sf = GLOBALS['mot_red_sf']
    sel_tweezer = GLOBALS['tweezers']

    sel_fluo_image = GLOBALS['fluo_image']
    sel_abs_image = GLOBALS['abs_image']

    sel_imaging_beam = GLOBALS['imaging_beam'] #'abs', 'tweez', '3Dmot'

    sel_camera_fluo = GLOBALS['camera_fluo'] #'andor', 'orca', 'basler_abs', 'basler_fluo'
    sel_camera_abs = GLOBALS['camera_abs'] #'basler_abs', 'andor', 'basler_fluo'
    sel_table_red=GLOBALS['table_red']

Orca_Camera.camera_attributes['EXPOSURE TIME']=0.05

start()
TABLE_MODE_ON('RedMOT', t)
t+=dt
set_MOGLABS_ready(t)
t+=dt
t=set_CompCoils(t)
exposure_time=10000*usec
t+=500*msec

ii=0
for i in range(0,GLOBALS['n_loop']):

    COILScomp_SwitchON_TTL(t, True)
    set_CompCoils(t+5*us)    

    MOT_Red3D_Switch_TTL(t, True)      #Global rf switch
    t+=dt

    if shieldSingle:
        if sel_table_red:
            NEW_TABLE_LINE('RedMOT', t, GLOBALS['Red_MOT_Frq']/1e6, 29.6)
            TABLE_MODE_OFF('RedMOT', t+GLOBALS['loadTime_BlueMOT'])
        else:
            MOT_Red3D_AOM_TTL(t, True)   
            MOT_Red3D_AOM_TTL(t+GLOBALS['loadTime_BlueMOT'], False)    
        t+=3*dt
        MOT_Red3D_multiFrq_TTL(t, False) 
        MOT_Red3D_singleFrq_TTL(t, True) 

    if shieldMulti:
        MOT_Red3D_AOM_TTL(t, False)     
        t+=dt
        MOT_Red3D_multiFrq_TTL(t, True) 
        MOT_Red3D_singleFrq_TTL(t, False) 

        MOT_Red3D_multiFrq_TTL(t+GLOBALS['loadTime_BlueMOT'], False) 

    ##### BLUE MOT #################
    if sel_mot_blue:
        print("Blue MOT")
    
        t=BlueMot_load(t, GLOBALS['loadTime_BlueMOT'])

        MOT_Blue2D_AOM_TTL(t-GLOBALS['TwoD_DELAY']+dt, False)
        MOT_Blue3D_AOM_TTL(t, False)
        t+=dt
        MOT_Blue3D_Shutter_TTL(t-1*msec, True)

        t+=dt
        COILSmain_Voltage(t, 0)
        t+=dt
        COILSmain_Current(t,0)
        t+=1*usec # the switch needs a 1 usec delay from the power supply switch-off
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

        t+=dt
    
        if sel_mot_red_sf:
            ##### SINGLE RED MOT #################    
            if sel_table_red:
                NEW_TABLE_LINE('RedMOT', t, GLOBALS['Red_MOT_Frq']/1e6, GLOBALS['Red_MOT_Pow'])
            else:
                MOT_Red3D_AOM_TTL(t, True)     
            t+=3*dt
            MOT_Red3D_singleFrq_TTL(t, True)
            t+=dt    
            # Orca_Camera_trigger.go_high(t) # Same channel as the Andor triggers also Orca now
            # Orca_Camera_trigger.go_low(t+100*usec)  
            Orca_Labscript_delay= 8.3*msec
            # t+=Orca_Camera.expose(t-Orca_Labscript_delay,'cleaning-shot', trigger_duration=100, saving=False)+Orca_Labscript_delay

            t+=dt   
            t+=GLOBALS['MOT_RED_SF_duration']
            MOT_Red3D_Switch_TTL(t, False)       
            MOT_Red3D_singleFrq_TTL(t, False)
            t+=dt

        #### RED MOT Turn Off
        COILSmain_Current(t, 0)
        t+=dt 
        COILSmain_SwitchON_TTL(t, False)
        t+=dt


        if sel_tweezer:
            ##### Tweezers loading #################
            t-=GLOBALS['Tweezer_duration']
            Twizzi_Switch_TTL(t, True)
            t+=GLOBALS['Tweezer_duration']

            t+=GLOBALS['FluoImgPulse_duration'] # tweezer stays on during fluo imaging
            t+=50*ms  #"TOF" Only to see the atoms in tweezers and the atoms in the red mot expand, this is a variable to be adjusted, minimum was 6ms to see minimal atoms, 10ms was a good value
            Twizzi_Switch_TTL(t, False)
            t+=dt

    ##### ALL OFF #################

    if sel_fluo_image:
        t_ahead_fluoimag = GLOBALS['FluoImgPulse_duration']#+5*dt # matches RedMot single freq duration comprehensive of delay introduced by the coils switch-off
        #t_ahead_fluoimag = GLOBALS['MOT_RED_duration']+100*msec # to see Blue MOT
        t-=t_ahead_fluoimag ########### TIME MACHINE  ############################ for Fluorescence
        
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
            # Andor camera needs 20 ms to clean sensor from previously collected light
            # Andor camera is controlled by Andor Solis
            andor_trigger_delay=20*us # it was originally at 100us but below under 'sel_abs_image' it is 20us so we (Vlad and Shawn) set it here to 20us
            Andor_Camera_fluo_readout=(1024*1024/1e6*sec+1024*2.2*usec)+100*msec # Horizontal readout + vertical shift times + buffer
            Orca_Camera_trigger.go_high(t-andor_trigger_delay)
            Orca_Camera_trigger.go_low(t-andor_trigger_delay+100*usec)

            t+=GLOBALS['FluoImgPulse_duration'] + Andor_Camera_fluo_readout

        elif sel_camera_fluo=='orca':
            orca_trigger_delay=7.2*usec*(4+1) + 4*usec # (4+1)*7us is in the manual as the longest delay + jitter pg. 49/82; we add 4us as an additonal buffer (total 40us)
            Orca_Camera_fluo_readout=(2304/2)*7.2*usec + (1/17.6)*sec # For USB, rolling shutter timing + inverse max frame rate (fps) at 4096x2304 pixels the readout time is 1/17.6 (for the whole image to be readout) pg. 60/82 of manual
            Orca_Labscript_delay= 8.3*msec

            Orca_Camera_trigger.go_high(t-orca_trigger_delay) 
            Orca_Camera_trigger.go_low(t-orca_trigger_delay+100*usec) 
                
            # t+=Orca_Camera.expose(t-orca_trigger_delay-Orca_Labscript_delay,'TweezFluo', trigger_duration=10, saving=True)+orca_trigger_delay+Orca_Labscript_delay

            Basler_Camera_extra_trigger.go_high(t-400*usec-5*usec)
            Basler_Camera_extra_trigger.go_low(t+10*usec)

            t+=GLOBALS['FluoImgPulse_duration'] + Orca_Camera_fluo_readout

        elif sel_camera_fluo=='basler_abs':
            # Basler_Camera_abs_trigger.go_high(t-100*usec-5*usec)
            # Basler_Camera_abs_trigger.go_low(t+1*msec)
            Basler_Camera_abs.expose(t-100*usec+5*usec,'Fluo', frametype='tiff')

        elif sel_camera_fluo=='basler_fluo':
            # Basler_Camera_fluo_trigger.go_high(t-100*usec-5*usec)
            # Basler_Camera_fluo_trigger.go_low(t+1*msec)
            Basler_Camera_extra_trigger.go_high(t-400*usec-5*usec)
            Basler_Camera_extra_trigger.go_low(t+100*usec) 
            # Basler camera for fluorescence is controlled by Pylon Viewer
            # Basler_Camera_fluo.expose(t-100*usec+5*usec,'Fluo', frametype='tiff')
       
        t+=t_ahead_fluoimag ############### TIME MACHINE  ############################

    t+=GLOBALS['TOF']# wait for time of flight
    
    if sel_abs_image:
        if sel_camera_abs=='andor':
            andor_trigger_delay=20*usec
            Andor_Camera_abs_readout=(1024*1024/30e6*sec+1024*2.2*usec)+30*msec # Horizontal readout + vertical shift times + buffer
            beam_duration = 500*usec

            # Orca_Camera_trigger.go_high(t-andor_trigger_delay)
            # Orca_Camera_trigger.go_low(t-andor_trigger_delay+100*usec)
            t+=dt
            # basler_trigger_delay=100*usec+5*usec #100 for camera activation + 5 as safety buffer
            # Basler_Camera_fluo_trigger.go_high(t-basler_trigger_delay)
            # Basler_Camera_fluo_trigger.go_low(t+1*msec)
            # t+=dt
            BlueImagingTweez_AOM_TTL(t, True)
            BlueImagingTweez_AOM_TTL(t+beam_duration, False)
            t+=beam_duration+Andor_Camera_abs_readout
            # Orca_Camera_trigger.go_high(t-andor_trigger_delay)
            # Orca_Camera_trigger.go_low(t-andor_trigger_delay+100*usec)
            BlueImagingTweez_AOM_TTL(t, True)
            BlueImagingTweez_AOM_TTL(t+beam_duration, False)
            t+=beam_duration+Andor_Camera_abs_readout
            # Orca_Camera_trigger.go_high(t-andor_trigger_delay)
            # Orca_Camera_trigger.go_low(t-andor_trigger_delay+100*usec)
            t+=beam_duration+Andor_Camera_abs_readout

        elif sel_camera_abs =='basler_abs':
            t=take_absorbImaging(t, GLOBALS['AbsImgPulse_duration'])

    t+=500*us
    Twizzi_Switch_TTL(t, False)
    t+=dt
    COILScomp_SwitchON_TTL(t, False)
    # setoff_CompCoils(t)
    t+=10*us

stop(t+GLOBALS['stop_buffering_time'])