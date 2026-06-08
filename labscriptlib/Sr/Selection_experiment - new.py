# originates from Absorption_BlueRed_MOT.py
#___________________________________________________________________________________#
from labscript import start, stop #                                                 |
from labscript_utils import import_or_reload #                                      |
import_or_reload('labscriptlib.Sr.SUB_ROUTINES') #                                  |
from labscriptlib.Sr.SUB_ROUTINES import * #                                        |
#\______________________________ GENERAL LIBRARIES ________________________________/#

if True: ## Selects ##
    shieldSingle = GLOBALS['ShieldSingle']
    shieldMulti = GLOBALS['ShieldMulti']

    sel_mot_blue = GLOBALS['mot_blue']
    sel_mot_red = GLOBALS['mot_red']
    sel_mot_red_sf = GLOBALS['mot_red_sf']
    sel_tweezer = GLOBALS['tweezers']

    sel_fluo_image = GLOBALS['imaging_fluo']
    sel_abs_image = GLOBALS['imaging_abs']

    sel_imaging_beam = GLOBALS['beam_imaging'] #'abs', 'tweez', '3Dmot'

    sel_camera_fluo = GLOBALS['camera_fluo'] #'andor', 'orca', 'basler_abs', 'basler_fluo'
    sel_camera_abs = GLOBALS['camera_abs'] #'basler_abs', 'andor', 'basler_fluo'
    sel_table_red=GLOBALS['table_red']

    orca_trigger_delay=7.2*usec*(4+1) + 4*usec # (4+1)*7us is in the manual as the longest delay + jitter pg. 49/82; we add 4us as an additonal buffer (total 40us)
    Orca_Camera_fluo_readout=(2304/2)*7.2*usec + (1/17.6)*sec # For USB, rolling shutter timing + inverse max frame rate (fps) at 4096x2304 pixels the readout time is 1/17.6 (for the whole image to be readout) pg. 60/82 of manual
    Orca_Labscript_delay= 8.3*msec
    if co:
        Orca_Camera.camera_attributes['EXPOSURE TIME']=GLOBALS['FluoImaging_duration']*1e-6
        if GLOBALS['Orca_ROI']=='full':
            Orca_Camera.camera_attributes['SUBARRAY MODE']=2
            Orca_Camera.camera_attributes['SUBARRAY HSIZE']=4096.0
            Orca_Camera.camera_attributes['SUBARRAY VSIZE']=2304.0
            Orca_Camera.camera_attributes['SUBARRAY HPOS']=0
            Orca_Camera.camera_attributes['SUBARRAY VPOS']=0
        elif GLOBALS['Orca_ROI']=='mot':
            Orca_Camera.camera_attributes['SUBARRAY MODE']=2
            Orca_Camera.camera_attributes['SUBARRAY HSIZE']=1000 #x
            Orca_Camera.camera_attributes['SUBARRAY VSIZE']=1000 #y
            Orca_Camera.camera_attributes['SUBARRAY HPOS']=425*4
            Orca_Camera.camera_attributes['SUBARRAY VPOS']=100*4
        elif GLOBALS['Orca_ROI']=='tweez':
            Orca_Camera.camera_attributes['SUBARRAY MODE']=2
            # Orca_Camera.camera_attributes['SUBARRAY HSIZE']=100 #x
            # Orca_Camera.camera_attributes['SUBARRAY VSIZE']=100 #y
            # Orca_Camera.camera_attributes['SUBARRAY HPOS']=2320
            # Orca_Camera.camera_attributes['SUBARRAY VPOS']=804
            Orca_Camera.camera_attributes['SUBARRAY HSIZE']=100 #x
            Orca_Camera.camera_attributes['SUBARRAY VSIZE']=100 #y
            Orca_Camera.camera_attributes['SUBARRAY HPOS']=530*4
            Orca_Camera.camera_attributes['SUBARRAY VPOS']=206*4
            
start() 
# Twizzi_Switch_TTL(t, True)      #temporary 
t+=dt
TABLE_MODE_ON('RedMOT', t)
t+=dt
TABLE_MODE_ON('Sisyphus', t)
t+=dt
set_MOGLABS_ready(t)
t+=dt
t=set_CompCoils(t, "ON")
# t+=500*msec
t+=200*msec
Shutter_ImagingBlue.go_high(t) 

for i in range(0,GLOBALS['n_loop']):

    t+=5*dt
    COILScomp_SwitchON_TTL(t, True)
    set_CompCoils(t+5*us, "ON")    
    MOT_Red3D_Switch_TTL(t, True)      #Global rf switch
    t+=dt
    Tweezers_AOM_TTL(t,True)
    Sisyphus_AOM_TTL(t,False)
    t+=dt
    Shutter_ImagingBlue.go_low(t+5*us)
    t+=5*ms
    Setpoint_imaging.constant(t,2.5)
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
    ##### BLUE MOT #################
    
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
            t+=dt    
            if co:
                # t+=Orca_Camera.expose(t-2*Orca_Labscript_delay,'cleaning-shot', trigger_duration=10, saving=False)+orca_trigger_delay+Orca_Labscript_delay
                aa=0
            else:
                Orca_Camera_trigger.go_high(t) 
                Orca_Camera_trigger.go_low(t+100*usec) 

            t+=dt   
            t+=GLOBALS['MOT_RED_SF_duration']
            if True: #cooling by ramping down RED beam power
                NEW_TABLE_LINE('RedMOT', t, GLOBALS['Red_MOT_Frq']/1e6, GLOBALS['Red_MOT_Pow']*9/10)
                t+=GLOBALS['MOT_RED_SF_duration']/10
                NEW_TABLE_LINE('RedMOT', t, GLOBALS['Red_MOT_Frq']/1e6, GLOBALS['Red_MOT_Pow']*8.5/10)
                t+=GLOBALS['MOT_RED_SF_duration']/10
                NEW_TABLE_LINE('RedMOT', t, GLOBALS['Red_MOT_Frq']/1e6, GLOBALS['Red_MOT_Pow']*8/10)
                t+=GLOBALS['MOT_RED_SF_duration']/10
                # NEW_TABLE_LINE('RedMOT', t, GLOBALS['Red_MOT_Frq']/1e6, GLOBALS['Red_MOT_Pow']*7/10)
                t+=GLOBALS['MOT_RED_SF_duration']/8
                # NEW_TABLE_LINE('RedMOT', t, GLOBALS['Red_MOT_Frq']/1e6, GLOBALS['Red_MOT_Pow']*6/10)

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
            t-=GLOBALS['TweezerLoading_duration']
            Twizzi_Switch_TTL(t, True)                
            t+=GLOBALS['TweezerLoading_duration']
            
            #cooling before first image (lots of atoms)

            # NEW_TABLE_LINE('Sisyphus', t, GLOBALS['Sisyphus_Frq']/1e6, GLOBALS['Sisyphus_Pow'])
            NEW_TABLE_LINE('Sisyphus', t, (GLOBALS['Red_MOT_Frq']+0.5*GLOBALS['Sisyphus_Frq'])/1e6, GLOBALS['Sisyphus_Pow'])
            t+=dt
            t+=5*dt
            Sisyphus_AOM_TTL(t,True)
            t+=GLOBALS['TweezerCooling_duration']
            Sisyphus_AOM_TTL(t,False)
            # t+=100*ms

            if GLOBALS['LAC']: 
                

                Setpoint_imaging.constant(t-5*ms,-3)
                t+=dt
                Shutter_ImagingBlue.go_high(t-3*ms)
                # t=-10*ms
                tt=t
                while tt-t < GLOBALS['LAC_duration']:
                    delta_cooling=2*ms
                    tt+=delta_cooling
                    Setpoint_imaging.constant(tt+dt+5*us,GLOBALS['LACPower_SetPoint'])
                    delta_imaging=1*ms
                    tt+=delta_imaging
                    Setpoint_imaging.constant(tt,-0.5)


                # t+=dt
                # Setpoint_imaging.constant(t,GLOBALS['LACPower_SetPoint'])
                # t+=dt
                t+=5*dt
                # NEW_TABLE_LINE('Sisyphus', t, GLOBALS['LAC_Frq']/1e6, GLOBALS['LAC_Pow'])
                NEW_TABLE_LINE('Sisyphus', t, (GLOBALS['Red_MOT_Frq']+0.5*GLOBALS['LAC_Frq'])/1e6, GLOBALS['LAC_Pow'])
                t+=dt
                Sisyphus_AOM_TTL(t,True)
                t+=3*dt
                t+=GLOBALS['LAC_duration']
                t+=3*dt
                # Setpoint_imaging.constant(t,-3)
                # Shutter_ImagingBlue.go_low(t-3*ms)
                # t+=dt
                Sisyphus_AOM_TTL(t,False)
            # TABLE_MODE_OFF('Sisyphus', t)
            t+=dt
            #Sisyphus_AOM_TTL(t,False)
            #t+=dt
            # NEW_TABLE_LINE('Sisyphus', t, GLOBALS['SisyphusImg_Frq']/1e6, GLOBALS['SisyphusImg_Pow'])
            NEW_TABLE_LINE('Sisyphus', t, (GLOBALS['Red_MOT_Frq']+0.5*GLOBALS['SisyphusImg_Frq'])/1e6, GLOBALS['SisyphusImg_Pow'])
            t+=GLOBALS['holdTime_fluoImg'] #to not see mot fluo # wait for the fluo imaging to evaluate the trap lifetime
            #Sisyphus_AOM_TTL(t,False)
            t+=GLOBALS['FluoImaging_duration'] # tweezer stays on during fluo imaging
            # TABLE_MODE_OFF('Sisyphus', t)
            # t+=20*ms  #"TOF" Only to see the atoms in tweezers and the atoms in the red mot expand, this is a variable to be adjusted, minimum was 6ms to see minimal atoms, 10ms was a good value
            t+=dt

    ##### ALL OFF #################

    if sel_fluo_image:
    #     ImagingBeam.DDS.setfreq(dt, GLOBALS['ImagingFluo_Frq']/1e6*1e3)
    #     ImagingBeam.DDS.setamp(dt, GLOBALS['ImagingFluo_Pow']*1e2)

        t_ahead_fluoimag = GLOBALS['QuantizAxis_ramp_duration'] + GLOBALS['FluoImaging_duration'] + 10*dt # matches RedMot single freq duration comprehensive of delay introduced by the coils switch-off
        #t_ahead_fluoimag = GLOBALS['MOT_RED_duration']+100*msec # to see Blue MOT

        t-=t_ahead_fluoimag ########### TIME MACHINE  ############################ for Fluorescence

        # Ramp selected compensation coils to value that sets Quantization axis for imaging
        if GLOBALS['QuantumAxis'] and sel_tweezer:set_CompCoils_QuantizationAxis(t-GLOBALS['QuantizAxis_ramp_duration'], "ON", GLOBALS['QuantizAxis_ramp_duration'], v_step_size=0.01)

        if sel_imaging_beam=="abs":
            if sel_tweezer:
                delta_imaging=GLOBALS['FluoImgPulse_Dt']
                delta_cooling=GLOBALS['FluoImgCooling_Dt']
                tt=t
                Setpoint_imaging.constant(t-5*ms,-3)
                Shutter_ImagingBlue.go_high(t-3*ms)
                Sisyphus_AOM_TTL(t,True)
                # NEW_TABLE_LINE('Sisyphus', t, (GLOBALS['Red_MOT_Frq']+0.5*GLOBALS['SisyphusImg_Frq'])/1e6, GLOBALS['SisyphusImg_Pow'])
                # TABLE_MODE_OFF('Sisyphus', t+ GLOBALS['FluoImaging_duration']) 
                # TABLE_MODE_OFF('Sisyphus', tt) 
                # NEW_TABLE_LINE('Sisyphus', t, GLOBALS['SisyphusImg_Frq']/1e6, GLOBALS['SisyphusImg_Pow'])
                # TABLE_MODE_OFF('Sisyphus', t + GLOBALS['FluoImaging_duration'])
                # Sisyphus_AOM_TTL(t+GLOBALS['FluoImaging_duration'],False)
                # if not GLOBALS['FluoCoolingPulsing']: #continous cooling during fluorescence
                    # NEW_TABLE_LINE('Sisyphus', t, (GLOBALS['SisyphusImg_Frq'])/1e6, GLOBALS['SisyphusImg_Pow'])
                    # TABLE_MODE_O
                    # ('Sisyphus', t + GLOBALS['FluoImaging_duration'])
                print(f"Start Sisyphus: {t} us")
                while tt-t < GLOBALS['FluoImaging_duration']:
                    if GLOBALS['FluoCoolingPulsing']:  #alternating cooling during fluorescence
                        NEW_TABLE_LINE('Sisyphus', tt+dt, (GLOBALS['Red_MOT_Frq']+0.5*GLOBALS['SisyphusImg_Frq'])/1e6, GLOBALS['SisyphusImg_Pow'])
                        tt+=delta_cooling
                        TABLE_MODE_OFF('Sisyphus', tt) 
                    else:
                        tt+=delta_cooling
                    # BlueImaging_AOM_TTL(tt+dt,True)
                    Setpoint_imaging.constant(tt+dt+5*us,GLOBALS['ImagingFluo_SetPoint'])
                    tt+=delta_imaging
                    # BlueImaging_AOM_TTL(tt, False)
                    # Setpoint_imaging.constant(tt+5*us,0.1)
                    Setpoint_imaging.constant(tt,-0.5)
                Setpoint_imaging.constant(tt,-0.5)
                Shutter_ImagingBlue.go_low(tt+5*us)
                Setpoint_imaging.constant(tt+5*ms,GLOBALS['ImagingFluo_SetPoint'])
                t+=GLOBALS['FluoImaging_duration'] 
                t+=5*ms
                print(t)
                print(tt)
                if GLOBALS['second_shot']:
                    NEW_TABLE_LINE('Sisyphus', t+5*us, (GLOBALS['Red_MOT_Frq']+0.5*GLOBALS['SisyphusImg_Frq'])/1e6, GLOBALS['SisyphusImg_Pow'])
                    print('two shot')
                else:
                    Sisyphus_AOM_TTL(t,False)
                    NEW_TABLE_LINE('Sisyphus', t+5*us, (GLOBALS['Red_MOT_Frq']+0.5*GLOBALS['SisyphusImg_Frq'])/1e6, GLOBALS['SisyphusImg_Pow']) #fixes time duration bug
                    TABLE_MODE_OFF('Sisyphus', t+ GLOBALS['FluoImaging_duration']+delta_cooling)  #solution that turns off sysiphus beam
                    

                print(f"End Sisyphus: {tt} us")
                print(f"FluoImaging_duration: {GLOBALS['FluoImaging_duration']} us")
            else:
                BlueImaging_AOM_TTL(t,True)
                BlueImaging_AOM_TTL(t+GLOBALS['FluoImaging_duration'], False)
                # Setpoint_imaging.constant(t-2.2*ms,0)
                # Shutter_imagingBlue.go_low(tt-2.2*ms)
                # Setpoint_imaging.constant(t,GLOBALS['ImagingFluo_SetPoint'])
                # Setpoint_imaging.constant(t+GLOBALS['FluoImaging_duration'], 0)
                # Shutter_imagingBlue.go_high(t-5.5*ms)
                # Setpoint_imaging.constant(t,GLOBALS['ImagingFluo_SetPoint'])
                
            # def imaging_PID_mode(t, valore_setpoint, durata):    

        elif sel_imaging_beam=='tweez':
            BlueImagingTweez_AOM_TTL(t, True)
            BlueImagingTweez_AOM_TTL(t+GLOBALS['FluoImaging_duration']+dt, False)
        elif sel_imaging_beam=='3Dmot':
            MOT_Blue3D_AOM_TTL(t, True)
            MOT_Blue3D_AOM_TTL(t+GLOBALS['FluoImaging_duration']+dt, False)
        
        if sel_camera_fluo=='andor': 
            # Andor camera needs 20 ms to clean sensor from previously collected light
            # Andor camera is controlled by Andor Solis
            andor_trigger_delay=20*us # it was originally at 100us but below under 'sel_abs_image' it is 20us so we (Vlad and Shawn) set it here to 20us
            Andor_Camera_fluo_readout=(1024*1024/1e6*sec+1024*2.2*usec)+100*msec # Horizontal readout + vertical shift times + buffer
            Orca_Camera_trigger.go_high(t-andor_trigger_delay)
            Orca_Camera_trigger.go_low(t-andor_trigger_delay+100*usec)

            t+=GLOBALS['FluoImaging_duration'] + Andor_Camera_fluo_readout
        elif sel_camera_fluo=='orca':
            t-= GLOBALS['FluoImaging_duration']
            if co:
                t+=Orca_Camera.expose(t+5*msec-orca_trigger_delay-Orca_Labscript_delay+20*ms,'TweezFluo', trigger_duration=10, saving=True)+orca_trigger_delay+Orca_Labscript_delay #+5 for sync with fluo
            else:
                Orca_Camera_trigger.go_high(t-orca_trigger_delay) 
                Orca_Camera_trigger.go_low(t-orca_trigger_delay+100*usec) 

            Basler_Camera_extra_trigger.go_high(t-400*usec-5*usec)
            Basler_Camera_extra_trigger.go_low(t+10*usec)

            t+=GLOBALS['FluoImaging_duration'] + Orca_Camera_fluo_readout
        elif sel_camera_fluo=='basler_abs':
            Basler_Camera_abs.expose(t-100*usec+5*usec,'Fluo', frametype='tiff')
        elif sel_camera_fluo=='basler_fluo':
            if cb_fluo:
                Basler_Camera_fluo.expose(t-100*usec+5*usec,'Fluo', frametype='tiff')
            else:
                Basler_Camera_fluo_trigger.go_high(t-100*usec-5*usec)
                Basler_Camera_fluo_trigger.go_low(t+1*msec)
            Basler_Camera_extra_trigger.go_high(t-400*usec-5*usec)
            Basler_Camera_extra_trigger.go_low(t+100*usec)
       
        t+=t_ahead_fluoimag ############### TIME MACHINE  ############################
        if GLOBALS['QuantumAxis'] and sel_tweezer:set_CompCoils_QuantizationAxis(t, "OFF", GLOBALS['QuantizAxis_ramp_duration'] )

    t+=GLOBALS['TOF'] # wait for time of flight
    
    if GLOBALS['second_shot']:
        t+=GLOBALS['holdTime_between_images']
        print('ciao')
        if GLOBALS['release_recapture']:
            print('release them')
            Tweezers_AOM_TTL(t+dt,True)
            Twizzi_Switch_TTL(t, False)
            t+=GLOBALS['release_time']
            print(GLOBALS['release_time'])
            Twizzi_Switch_TTL(t, True) 
        # NEW_TABLE_LINE('Sisyphus', t-Orca_Camera_fluo_readout-GLOBALS['FluoImaging_duration']-orca_trigger_delay-Orca_Labscript_delay, (GLOBALS['Red_MOT_Frq']+0.5*GLOBALS['SisyphusImg_Frq'])/1e6, GLOBALS['SisyphusImg_Pow'])
        # t+=dt
        # Sisyphus_AOM_TTL(t-Orca_Camera_fluo_readout-GLOBALS['FluoImaging_duration']-orca_trigger_delay-Orca_Labscript_delay-10*ms,True)
        # t+=dt
        # Sisyphus_AOM_TTL(t,False)
        # t+=dt
        NEW_TABLE_LINE('Sisyphus', t, (GLOBALS['Red_MOT_Frq']+0.5*GLOBALS['SisyphusImg_Frq_2nd'])/1e6, GLOBALS['SisyphusImg_Pow_2nd'])
        tt=t
        # Sisyphus_AOM_TTL(t,True)
    
        # TABLE_MODE_OFF('Sisyphus', t+GLOBALS['FluoImaging_duration'])
        # t+=dt
        # Sisyphus_AOM_TTL(t+GLOBALS['FluoImaging_duration'],False)
        
        Setpoint_imaging.constant(t-5*ms,-3)
        Shutter_ImagingBlue.go_high(t-3*ms)
        while tt-t < GLOBALS['FluoImaging_duration']:
            delta_cooling=GLOBALS['FluoImgCooling_Dt']
            tt+=delta_cooling
            Setpoint_imaging.constant(tt+dt+5*us,GLOBALS['ImagingFluo_SetPoint_2nd'])
            delta_imaging=GLOBALS['FluoImgPulse_Dt']
            tt+=delta_imaging
            Setpoint_imaging.constant(tt,-0.5)
        
        
        Setpoint_imaging.constant(tt,-0.5)
        Shutter_ImagingBlue.go_low(tt+5*us)
        Setpoint_imaging.constant(tt+5*ms,GLOBALS['ImagingFluo_SetPoint_2nd'])               
        t+=GLOBALS['FluoImaging_duration'] 
        # t+=5*ms
        Sisyphus_AOM_TTL(t,False)
        # NEW_TABLE_LINE('Sisyphus', t+5*us, (GLOBALS['Red_MOT_Frq']+0.5*GLOBALS['SisyphusImg_Frq_2nd'])/1e6, GLOBALS['SisyphusImg_Pow_2nd'])
        TABLE_MODE_OFF('Sisyphus', t+GLOBALS['FluoImaging_duration']+delta_cooling-200*ms)  #solution that turns off sysiphus beam
                
        # t+=Orca_Camera.expose(t-2*Orca_Labscript_delay,'second-shot', trigger_duration=10, saving=True)+orca_trigger_delay+Orca_Labscript_delay
        t+=Orca_Camera.expose(t+5*msec-orca_trigger_delay-Orca_Labscript_delay-GLOBALS['FluoImaging_duration']+20*ms ,'second-shot', trigger_duration=10, saving=True)+orca_trigger_delay+Orca_Labscript_delay #+5 for sync with fluo

    if sel_abs_image:
        # ImagingBeam.DDS.setfreq(dt,GLOBALS['Imaging_Frq']/1e6*1e3)
        # ImagingBeam.DDS.setamp(dt, GLOBALS['Imaging_Pow']*1e2)
        # delayPID = 3.5*ms
        # t-=4.5*ms
        # Setpoint_imaging.constant(t,-1) #turning off AOM
        # t+=5*us
        # Shutter_ImagingBlue.go_high(t) 
        # t+=delayPID 
        # Setpoint_imaging.constant(t,GLOBALS['ImagingFluo_SetPoint'])# turning on the AOM with the external setpoint considering delay
        # # Setpoint_imaging.constant(t-200*us,0.1)
        # t+=dt                                #constant delay to get to the aom activation
        # t+=GLOBALS['AbsImgPulse_duration']
        # Setpoint_imaging.constant(t,-1) #turning off AOM
        
        # Shutter_ImagingBlue.go_low(t+50*us)
        # t+=5*ms
        # Setpoint_imaging.constant(t,5)
        # t+=dt



        # Test.constant(t-10*ms,0) #turning off AOM
        # t+=5*us
        # Shutter_ImagingBlue.go_high(t-2.5*ms) 
        
        # Test.constant(t,GLOBALS['ImagingFluo_SetPoint'])# turning on the AOM with the external setpoint considering delay
        # # Setpoint_imaging.constant(t-200*us,0.1)
        # t+=GLOBALS['AbsImgPulse_duration']
        # Test.constant(t+1*us,0) #turning off AOM

        # Shutter_ImagingBlue.go_low(t+5*us)
        # t+=10*ms
        # Test.constant(t+1*us,1)

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

            trigger_delay=100*usec+5*usec+0.5*ms
            t-=3.9*ms
            Setpoint_imaging.constant(t-10*ms,-1) #turning off AOM
            t+=5*us
            Shutter_ImagingBlue.go_high(t-3*ms) 
            t+=dt                                 #constant delay to get to the aom activation
            Setpoint_imaging.constant(t+2.9*ms,GLOBALS['ImagingAbs_SetPoint'])# turning on the AOM with the external setpoint considering delay
            # Setpoint_imaging.constant(t-200*us,0.1)
            t+=Basler_Camera_abs.expose(t-trigger_delay,'Atoms', frametype='tiff')
            t+=GLOBALS['AbsImgPulse_duration']+4.0*ms
            Setpoint_imaging.constant(t+1*us,-1) #turning off AOM
            # Setpoint_imaging.constant(t-100*us,-1) #turning off AOM

            Shutter_ImagingBlue.go_low(t+5*us)
            t+=10*ms
            Setpoint_imaging.constant(t+1*us,5)
            t+=20*ms
            # trigger_delay=100*usec+5*usec #100 for camera activation + 5 as safety buffer
            Basler_Camera_abs_readout=4*120*msec # was at 120ms with small ROI, when enlarged changed to 200ms, still had issues capturing, changed to 480 and no issue
            t+=15*ms
            Setpoint_imaging.constant(t-10*ms,-1) #turning off AOM
            t+=5*us
            Shutter_ImagingBlue.go_high(t-3*ms) 
        
            Setpoint_imaging.constant(t+2.9*ms,GLOBALS['ImagingAbs_SetPoint'])# turning on the AOM with the external setpoint considering delay
            # Setpoint_imaging.constant(t-200*us,0.1)
            t+=Basler_Camera_abs.expose(t-trigger_delay,'Probe', frametype='tiff')
            t+=GLOBALS['AbsImgPulse_duration']+4*ms
            Setpoint_imaging.constant(t+1*us,-1) #turning off AOM

            Shutter_ImagingBlue.go_low(t+5*us)
            t+=10*ms
            Setpoint_imaging.constant(t+1*us,5)

            # BlueImaging_AOM_TTL(tt, True)
            # BlueImaging_AOM_TTL(tt+beam_duration, False)
            # tt+=Basler_Camera_abs.expose(tt-trigger_delay,'Atoms', frametype='tiff')
    
            # tt+=Basler_Camera_abs_readout 

            # BlueImaging_AOM_TTL(tt, True)
            # BlueImaging_AOM_TTL(tt+beam_duration, False)
            # tt+=Basler_Camera_abs.expose(tt-trigger_delay,'Probe', frametype='tiff')

            # tt+=Basler_Camera_abs_readout 

            # Basler_Camera_abs.expose(tt-trigger_delay,'Background', frametype='tiff')

            t+=Basler_Camera_abs_readout 
            t+=Basler_Camera_abs.expose(t-trigger_delay,'Background', frametype='tiff')
            t+=Basler_Camera_abs_readout 

    t+=500*us
    t+=250*ms
    
    # Twizzi_Switch_TTL(t, False)       #temporarily off
    # Tweezers_AOM_TTL(t+dt,False)
    Tweezers_AOM_TTL(t+dt,True)
    Twizzi_Switch_TTL(t, False)
    # Shutter_ImagingBlue.go_low(t+5*ms)
    t+=3*ms

stop(t+GLOBALS['stop_buffering_time'])