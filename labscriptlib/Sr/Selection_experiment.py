# originates from Absorption_BlueRed_MOT.py
#___________________________________________________________________________________#
from labscript import start, stop #                                                 |
from labscript_utils import import_or_reload #                                      |
import_or_reload('labscriptlib.Sr.SUB_ROUTINES') #                                  |
from labscriptlib.Sr.SUB_ROUTINES import GLOBALS #                                  |
from labscriptlib.Sr.SUB_ROUTINES import * #                                        |
#\______________________________ GENERAL LIBRARIES ________________________________/#

if True: ## Selects ##
    shieldSingle = GLOBALS['ShieldSingle']
    shieldMulti = GLOBALS['ShieldMulti']

    sel_mot_blue = GLOBALS['mot_blue']
    sel_mot_red = GLOBALS['mot_red']
    sel_mot_red_sf = GLOBALS['mot_red_sf']
    sel_tweezer = GLOBALS['tweezers']
    sel_tweezer_always_on = GLOBALS['tweezers_always_on']
    sel_fluo_image = GLOBALS['imaging_fluo']
    sel_abs_image = GLOBALS['imaging_abs']

    sel_imaging_beam = GLOBALS['beam_imaging'] #'abs', 'tweez', '3Dmot'

    sel_camera_fluo = GLOBALS['camera_fluo'] #'andor', 'orca', 'basler_abs', 'basler_fluo'
    sel_camera_abs = GLOBALS['camera_abs'] #'basler_abs', 'andor', 'basler_fluo'

    # orca_trigger_delay=7.2*usec*(4+1) + 4*usec # (4+1)*7us is in the manual as the longest delay + jitter pg. 49/82; we add 4us as an additonal buffer (total 40us)
    orca_trigger_delay=GLOBALS['orca_trigger_delay']
    Orca_Camera_fluo_readout=(2304/2)*7.2*usec + (1/17.6)*sec # For USB, rolling shutter timing + inverse max frame rate (fps) at 4096x2304 pixels the readout time is 1/17.6 (for the whole image to be readout) pg. 60/82 of manual
    Orca_Labscript_delay= 9*msec

    if co:
        Orca_Camera.camera_attributes['EXPOSURE TIME'] = GLOBALS['FluoImaging_duration'] * 1e-6

    Orca_Camera.camera_attributes['SUBARRAY MODE'] = 1

    if GLOBALS['Orca_ROI'] == 'full':
        Orca_Camera.camera_attributes['SUBARRAY HPOS'] = 0
        Orca_Camera.camera_attributes['SUBARRAY VPOS'] = 0
        Orca_Camera.camera_attributes['SUBARRAY HSIZE'] = 4096
        Orca_Camera.camera_attributes['SUBARRAY VSIZE'] = 2304

        Orca_Camera.camera_attributes['SUBARRAY MODE'] = 1

    elif GLOBALS['Orca_ROI'] == 'tweez':
        # Orca_preparation_time=0.5*ms
        Orca_Camera.camera_attributes['SUBARRAY HSIZE'] = 50*2
        Orca_Camera.camera_attributes['SUBARRAY VSIZE'] = 50*2
        Orca_Camera.camera_attributes['SUBARRAY HPOS'] = 2096
        Orca_Camera.camera_attributes['SUBARRAY VPOS'] = 940

        Orca_Camera.camera_attributes['SUBARRAY MODE'] = 2 ##add +=1ms to ORCA delay

    elif GLOBALS['Orca_ROI'] == 'mot':
        ##add +=1ms to ORCA delay
        Orca_Camera.camera_attributes['SUBARRAY HSIZE'] = 240 # 120*2
        Orca_Camera.camera_attributes['SUBARRAY VSIZE'] = 240 # 120*2
        Orca_Camera.camera_attributes['SUBARRAY HPOS'] =  1160 #1960
        Orca_Camera.camera_attributes['SUBARRAY VPOS'] =  820 #840

        Orca_Camera.camera_attributes['SUBARRAY MODE'] = 2

    elif GLOBALS['Orca_ROI'] == 'test':
        ##add +=1ms to ORCA delay
        Orca_Camera.camera_attributes['SUBARRAY HSIZE'] = 240*2
        Orca_Camera.camera_attributes['SUBARRAY VSIZE'] = 240*2
        Orca_Camera.camera_attributes['SUBARRAY HPOS'] = 640 * 4 - 120
        Orca_Camera.camera_attributes['SUBARRAY VPOS'] = 230*4 - 120

        Orca_Camera.camera_attributes['SUBARRAY MODE'] = 2
            

start()

t+=dt
TABLE_MODE_ON('RedMOT', t)
t+=dt
TABLE_MODE_ON('Sisyphus', t)
t+=dt
set_MOGLABS_ready(t)
t+=dt
t=set_CompCoils(t, "ON")
MOT_Blue3D_Shutter_TTL(t, True)   
# t+=dt +500*ms #+ Orca_preparation_time
t+=dt +0*ms #set to 10 ms to check




# t+=200*msec #check why this delay is needed
t+=0*msec #set to 10 ms to check
Shutter_ImagingBlue.go_low(t) 

for i in range(0,GLOBALS['n_loop']):

    t+=5*dt
    COILScomp_SwitchON_TTL(t, True)
    set_CompCoils(t+5*us, "ON")  
    # MOT_Red3D_Switch_TTL(t, True)      #Global rf switch. obsolete
    t+=dt
    Tweezers_AOM_TTL(t, True) #TODO: fix awg trigger
    t+=dt
    if sel_tweezer_always_on:
        Twizzi_Switch_TTL(t, False)
    else:
        Twizzi_Switch_TTL(t, True)
    t+=dt
    Re707_AOM_TTL(t, True)
    t+=dt
    Re679_AOM_TTL(t, True)
    t+=dt

    if shieldSingle:
        NEW_TABLE_LINE('RedMOT', t, GLOBALS['Red_MOT_Frq_fin']/1e6, GLOBALS['Red_MOT_Pow_fin'])

        t+=3*dt

        MOT_Red3D_multiFrq_TTL(t, False) 
        MOT_Red3D_singleFrq_TTL(t, True) 
        MOT_Red3D_singleFrq_TTL(t+GLOBALS['loadTime_BlueMOT'], False)

    if shieldMulti:
        # MOT_Red3D_AOM_TTL(t, False)     
        t+=dt
        # MOT_Red3D_AOM_TTL(t, True, mode='multiFrq')
        # MOT_Red3D_AOM_TTL(t+GLOBALS['loadTime_BlueMOT'], False)
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
        t+=3*dt
        MOT_Blue3D_AOM_TTL(t+1.6*msec, True)

        if not GLOBALS['repumpers_always_on']:
            t+=dt
            Re707_AOM_TTL(t, False)
            t+=dt
            Re679_AOM_TTL(t, False)
            t+=dt
        
        fluo_delay=10*msec

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
        COILSmain_Voltage(t, GLOBALS['coils_voltage_ctrl_red'])          #Turn on the COILSmain at 10 A, roughly 5 G/cm
        t+=dt 
        COILSmain_Current(t, GLOBALS['coils_current_ctrl_red'])          #Turn on the COILSmain at 10 A, roughly 5 G/cm
        ###########

        t+=GLOBALS['MOT_RED_BB_duration']
        MOT_Red3D_multiFrq_TTL(t, False)
        t+=dt

        if sel_mot_red_sf:
            ##### SINGLE RED MOT #################    
            n_steps=GLOBALS['Red_MOT_SF_nSteps']
            frq_i=GLOBALS['Red_MOT_Frq_ini'] #72.5e6#center of BroadBand Red MOT comb (MHz)
            frq_f=GLOBALS['Red_MOT_Frq_fin']
            pow_i=GLOBALS['Red_MOT_Pow_ini']
            pow_f=GLOBALS['Red_MOT_Pow_fin']
            red_duration=GLOBALS['MOT_RED_SF_duration']
            if n_steps==1:
                NEW_TABLE_LINE('RedMOT', t-5*usec, frq_f/1e6, pow_f)
                MOT_Red3D_singleFrq_TTL(t, True)
                t+=GLOBALS['MOT_RED_SF_duration']
            else:
                MOT_Red3D_singleFrq_TTL(t, True)
                for i in range(int(n_steps)):
                    NEW_TABLE_LINE('RedMOT', t-5*usec, (frq_i + (frq_f-frq_i)*i/n_steps)/1e6, pow_i + (pow_f-pow_i)*i/n_steps) #GLOBALS['Red_MOT_Pow_fin']+(n_steps-i)/n_steps*GLOBALS['Red_MOT_Pow_fin']*0.15
                    t+=red_duration/n_steps
            t+=dt    

            if True: #cooling by ramping down RED beam power
                NEW_TABLE_LINE('RedMOT', t, frq_f/1e6, pow_f*9/10)
                t+=red_duration/10
                NEW_TABLE_LINE('RedMOT', t, frq_f/1e6, pow_f*8.5/10)
                t+=red_duration/10
                NEW_TABLE_LINE('RedMOT', t, frq_f/1e6, pow_f*8/10)
                t+=red_duration/10
                # NEW_TABLE_LINE('RedMOT', t, frq_f/1e6, pow_f*7/10)
                t+=red_duration/8
                

            # MOT_Red3D_Switch_TTL(t, False)   #Global rf switch. obsolete     
            MOT_Red3D_singleFrq_TTL(t, False)
            t+=dt

            fluo_delay=GLOBALS['fluo_delay']

        #### RED MOT Turn Off
        COILSmain_Current(t, 0)
        t+=dt 
        COILSmain_SwitchON_TTL(t, False)
        # if GLOBALS['blow_atoms']:
        #     set_CompCoils_QuantizationAxis(t+dt+dt, "ON", GLOBALS['QuantizAxis_ramp_duration'], v_step_size=0.01)

        if GLOBALS['QuantumAxis']: 
            t += set_CompCoils_QuantizationAxis(t+dt, "ON", GLOBALS['QuantizAxis_ramp_duration'])
            if sel_tweezer:
                t+=15*msec

        if sel_tweezer:

            fluo_delay=10*msec
            ##### Tweezers loading #################
            t-=GLOBALS['TweezerLoading_duration']

            Twizzi_Switch_TTL(t, False)
            t+=dt
            # t-=500*ms
            awg_trigger.go_high(t) # Trigger the AWG to start the sequence
            awg_trigger.go_low(t + 2*usec) # Trigger the AWG to start the sequence
            Tweezers_AOM_TTL(t+dt, True)

            t+=GLOBALS['TweezerLoading_duration']
            #set_CompCoils(t+5*us, "OFF")    

            start_tweezer_time=t
            # Tweezers_AOM_TTL(t+dt, False)

            t+=4*dt 

            # Bfiled_test(t+dt, "ON")
       
            t+=4*dt 
            #cooling before first image (lots of atoms)

            # NEW_TABLE_LINE('Sisyphus', t, GLOBALS['Sisyphus_Frq']/1e6, GLOBALS['Sisyphus_Pow'])
            t += NEW_TABLE_LINE('Sisyphus', t, (GLOBALS['Red_MOT_Frq_fin']+0.5*GLOBALS['Sisyphus_Frq'])/1e6, GLOBALS['Sisyphus_Pow'], GLOBALS['TweezerCooling_duration']) #trigger half time to avoid interplay between 
            # t += 1000*usec



            if GLOBALS['LAC']: 
                # ImagingBeam.DDS.setfreq(t, GLOBALS['ImagingTweez_Frq']/1e6*1e3)
                # ImagingBeam.DDS.setamp(t, GLOBALS['blue_LAC_Pow']*1e2)
                t+=dt
                # BlueImaging_AOM_TTL(t,True) #blue cathalyzing
                

                t+=5*dt
                # NEW_TABLE_LINE('Sisyphus', t, GLOBALS['LAC_Frq']/1e6, GLOBALS['LAC_Pow'])
                t+=NEW_TABLE_LINE('Sisyphus', t, (GLOBALS['Red_MOT_Frq_fin']+0.5*GLOBALS['LAC_Frq'])/1e6, GLOBALS['LAC_Pow'], GLOBALS['LAC_duration'])
                t+=10*dt
                # t+=dt
                # # Sisyphus_AOM_TTL(t,True)
                # t+=3*dt
                # t+=GLOBALS['LAC_duration']
                # t+=3*dt
                # BlueImaging_AOM_TTL(t,False)
                t+=dt
                # Sisyphus_AOM_TTL(t,False)
            t+=4*dt 
            TABLE_MODE_OFF('Sisyphus', t)
            t+=dt

            
            t+=GLOBALS['holdTime_fluoImg'] #to not see mot fluo # wait for the fluo imaging to evaluate the trap lifetime
            t+=10*dt
            


    ##### ALL OFF #################  IMAGING SECTION STARTS HERE
    if not sel_tweezer:
        t += GLOBALS['TOF']  # wait for time of flight
        if GLOBALS['blow_atoms']:
            t+=NEW_TABLE_LINE('Sisyphus', t, (GLOBALS['Red_MOT_Frq_fin']+0.5*GLOBALS['Sisyphus_Frq'])/1e6, GLOBALS['Sisyphus_Pow'],2*ms)
            Sisyphus_AOM_TTL(t,True)
            Sisyphus_AOM_TTL(t+dt,False)
            TABLE_MODE_OFF('Sisyphus', t+5*dt)

        
    if sel_fluo_image:
        if not sel_abs_image and not sel_tweezer: # if no absorption imaging, we can use the same beam for fluorescence, otherwise we can change the frequency and power for fluorescence 
            ImagingBeam.DDS.setfreq(t, GLOBALS['ImagingFluo_Frq']/1e6*1e3)
            ImagingBeam.DDS.setamp(t, GLOBALS['ImagingFluo_Pow']*1e2)
            ImagingTweezBeam.DDS.setfreq(t,GLOBALS['ImagingFluo_Frq']/1e6*1e3)
            ImagingTweezBeam.DDS.setamp(t, GLOBALS['ImagingFluo_Pow']*1e2)

        t+=GLOBALS['FluoImaging_duration'] # tweezer or MOT stays on during fluo imaging

        t_ahead_fluoimag = GLOBALS['QuantizAxis_ramp_duration'] + GLOBALS['FluoImaging_duration'] + 10*dt # matches RedMot single freq duration comprehensive of delay introduced by the coils switch-off

        t-=t_ahead_fluoimag ########### TIME MACHINE  ############################ for Fluorescence

        # Ramp selected compensation coils to value that sets Quantization axis for imaging


        if sel_imaging_beam=="abs":
            if sel_tweezer:
                if not GLOBALS['repumpers_always_on']:
                    t+=dt
                    # Re707_AOM_TTL(t, True)
                    # t+=dt
                    # Re679_AOM_TTL(t, True)
                    t+=dt
                ImagingBeam.DDS.setfreq(t,GLOBALS['ImagingTweez_Frq']/1e6*1e3)
                ImagingBeam.DDS.setamp(t, GLOBALS['ImagingTweez_Pow']*1e2)
                print(GLOBALS['ImagingTweez_Frq'])

                delta_imaging=GLOBALS['FluoImgPulse_Dt']
                delta_cooling=GLOBALS['FluoImgCooling_Dt']
                tt=t
                Sisyphus_AOM_TTL(t,True)
                Sisyphus_AOM_TTL(t+dt,False)
                print(f"Start imaging Sisyphus: {t} us")
                NEW_TABLE_LINE('Sisyphus', t, (GLOBALS['Red_MOT_Frq_fin']+0.5*GLOBALS['SisyphusImg_Frq'])/1e6, GLOBALS['SisyphusImg_Pow'], GLOBALS['FluoImaging_duration'] )

                
                while tt-t < GLOBALS['FluoImaging_duration']:
                    if GLOBALS['FluoCoolingPulsing']:  #alternating cooling during fluorescence
                        NEW_TABLE_LINE('Sisyphus', tt+dt, (GLOBALS['Red_MOT_Frq_fin']+0.5*GLOBALS['SisyphusImg_Frq'])/1e6, GLOBALS['SisyphusImg_Pow'])
                        tt+=delta_cooling
                        TABLE_MODE_OFF('Sisyphus', tt) 
                    else:
                        tt+=delta_cooling
                    BlueImaging_AOM_TTL(tt+dt,True)
                    tt+=delta_imaging
                    BlueImaging_AOM_TTL(tt, False)

                TABLE_MODE_OFF('Sisyphus', tt)  #solution that turns off Sisyphus beam
                tt+=4*dt 

                #Sisyphus_AOM_TTL(t+dt+ GLOBALS['FluoImaging_duration']+delta_cooling,False)
                if not GLOBALS['repumpers_always_on']:
                    tt+=dt
                    # Re707_AOM_TTL(tt, False)
                    # tt+=dt
                    # Re679_AOM_TTL(tt, False)
                    tt+=dt

                # print(f"End Sisyphus: {tt} us")
                print(f"FluoImaging_duration: {GLOBALS['FluoImaging_duration']} us")
            else:
                if not sel_abs_image:
                    BlueImaging_AOM_TTL(t,True)
                    BlueImaging_AOM_TTL(t+GLOBALS['FluoImaging_duration'], False)
        elif sel_imaging_beam=='tweez':
            BlueImagingTweez_AOM_TTL(t, True)
            BlueImagingTweez_AOM_TTL(t+GLOBALS['FluoImaging_duration']+dt, False)
        elif sel_imaging_beam=='3Dmot':
            MOT_Blue3D_AOM_TTL(t, True)
            MOT_Blue3D_AOM_TTL(t+GLOBALS['FluoImaging_duration']+dt, False)
        
        if 'andor' in sel_camera_fluo: 
            # Andor camera needs 20 ms to clean sensor from previously collected light
            # Andor camera is controlled by Andor Solis
            andor_trigger_delay=20*us # it was originally at 100us but below under 'sel_abs_image' it is 20us so we (Vlad and Shawn) set it here to 20us
            Andor_Camera_fluo_readout=(1024*1024/1e6*sec+1024*2.2*usec)+100*msec # Horizontal readout + vertical shift times + buffer
            Orca_Camera_trigger.go_high(t-andor_trigger_delay)
            Orca_Camera_trigger.go_low(t-andor_trigger_delay+100*usec)
            camera_readout = Andor_Camera_fluo_readout

        if 'orca' in sel_camera_fluo:
            if co:
                Basler_Camera_extra_trigger.go_high(t-fluo_delay-1*msec) # Basler starts acquiring the image at the Falling edge of the trigger, we set it to be before the fluo pulse to make sure we acquire the whole pulse
                Basler_Camera_extra_trigger.go_low(t-fluo_delay+dt)
                exposure_duration = Orca_Camera.expose(t+4*msec-orca_trigger_delay-Orca_Labscript_delay,'TweezFluo', trigger_duration=10, saving=True)+orca_trigger_delay+Orca_Labscript_delay #+5 for sync with fluo
            else:
                exposure_duration = 100*usec
                Orca_Camera_trigger.go_high(t-orca_trigger_delay) 
                Orca_Camera_trigger.go_low(t-orca_trigger_delay + exposure_duration) 
                Basler_Camera_extra_trigger.go_high(t-500*usec)
                Basler_Camera_extra_trigger.go_low(t+1*msec)
            camera_readout=Orca_Camera_fluo_readout + exposure_duration

        if 'basler_abs' in sel_camera_fluo:
            Basler_Camera_abs.expose(t-100*usec+5*usec,'Fluo', frametype='tiff')
            camera_readout = 0

        if 'basler_fluo' in sel_camera_fluo:
            if cb_fluo:
                Basler_Camera_fluo.expose(t-100*usec+5*usec,'Fluo', frametype='tiff')
            else:
                Basler_Camera_fluo_trigger.go_high(t-100*usec-5*usec)
                Basler_Camera_fluo_trigger.go_low(t+1*msec)
            camera_readout = 0

        if 'basler_extra' in sel_camera_fluo:
            if cb_extra:
                Basler_Camera_extra.expose(t+500*usec+5*usec,'Fluo', frametype='tiff')
            else:
                Basler_Camera_extra_trigger.go_high(t-100*usec-5*usec)
                Basler_Camera_extra_trigger.go_low(t+1*msec)
            camera_readout = 0

        elif sel_camera_fluo=='orca_extra':
            Basler_Camera_extra.expose(t+500*usec+5*usec,'Fluo', frametype='tiff')
            t+=Orca_Camera.expose(t-orca_trigger_delay-Orca_Labscript_delay,'TweezFluo', trigger_duration=10, saving=True)+orca_trigger_delay+Orca_Labscript_delay #+5 for sync with fluo


        t+=GLOBALS['FluoImaging_duration'] + camera_readout

        t+=t_ahead_fluoimag ############### TIME MACHINE  ############################


    
    if GLOBALS['second_shot']:

        tt = t - Orca_Camera_fluo_readout - GLOBALS['FluoImaging_duration'] - orca_trigger_delay - Orca_Labscript_delay + 100*ms
        t0=tt

        Sisyphus_AOM_TTL(tt,True)
        Sisyphus_AOM_TTL(tt+dt,False)
        print(f"Start imaging Sisyphus: {tt} us")
        # NEW_TABLE_LINE('Sisyphus', tt, (GLOBALS['Red_MOT_Frq_fin']+0.5*GLOBALS['Sisyphus_Frq'])/1e6, GLOBALS['Sisyphus_Pow'], GLOBALS['FluoImaging_duration'] )
        NEW_TABLE_LINE('Sisyphus', tt, (GLOBALS['Red_MOT_Frq_fin']+0.5*GLOBALS['SisyphusImg_Frq'])/1e6, GLOBALS['SisyphusImg_Pow'])

        t+=Orca_Camera.expose(tt+5*msec,'second-shot', trigger_duration=10, saving=True)+orca_trigger_delay+Orca_Labscript_delay #+5 for sync with fluo

        while tt-t0 < GLOBALS['FluoImaging_duration']:
            if GLOBALS['FluoCoolingPulsing']:  #alternating cooling during fluorescence
                NEW_TABLE_LINE('Sisyphus', tt+dt, (GLOBALS['Red_MOT_Frq_fin']+0.5*GLOBALS['SisyphusImg_Frq'])/1e6, GLOBALS['SisyphusImg_Pow'])
                tt+=delta_cooling
                TABLE_MODE_OFF('Sisyphus', tt) 
            else:
                tt+=delta_cooling
            BlueImaging_AOM_TTL(tt+dt,True)
            tt+=delta_imaging
            BlueImaging_AOM_TTL(tt, False)

        TABLE_MODE_OFF('Sisyphus', tt)  #solution that turns off Sisyphus beam
        tt+=4*dt

        second_shot_duration=tt-t0
        print(f"second shot duration {second_shot_duration}")
        t+=second_shot_duration
        

    if sel_abs_image:
        if sel_fluo_image:
            t-=t_ahead_fluoimag+orca_trigger_delay+Orca_Labscript_delay+GLOBALS['FluoImaging_duration'] + Orca_Camera_fluo_readout
        ImagingBeam.DDS.setfreq(t,GLOBALS['ImagingAbs_Frq']/1e6*1e3)
        ImagingBeam.DDS.setamp(t, GLOBALS['ImagingAbs_Pow']*1e2)
        ImagingTweezBeam.DDS.setfreq(t,GLOBALS['ImagingTweez_Frq']/1e6*1e3)
        ImagingTweezBeam.DDS.setamp(t, GLOBALS['ImagingTweez_Pow']*1e2)
        # BlueImagingTweez_AOM_TTL(t, True)
        # BlueImagingTweez_AOM_TTL(t+GLOBALS['AbsImgPulse_duration']+dt, False)

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
    # 2*t+=250*ms #removed to meke the sequence faster... to be checked, why is this here?
    # Twizzi_Switch_TTL(t, False)
    if sel_tweezer_always_on:
        t+=+dt
        # Tweezers_AOM_TTL(t,True)
        # t+=+dt
        # Twizzi_Switch_TTL(t+dt, False)
    else:
        t+=+dt
        # Tweezers_AOM_TTL(t,False)
        t+=+dt
        Twizzi_Switch_TTL(t+dt, True)
    awg_trigger.go_high(t) # Trigger the AWG to start the sequence
    awg_trigger.go_low(t + 2*usec) # Trigger the AWG to start the sequence
    t+=3*ms
    #################  IMAGING SECTION ENDS HERE
    if not GLOBALS['repumpers_always_on']:
        t+=dt
        Re707_AOM_TTL(t, False)
        t+=dt
        Re679_AOM_TTL(t, False)
        t+=dt
    if GLOBALS['QuantumAxis']: t += set_CompCoils_QuantizationAxis(t, "OFF", GLOBALS['QuantizAxis_ramp_duration'] )

t=standby(t)
Shutter_ImagingBlue.go_high(t) 
t+=dt
# MOT_Blue3D_AOM_TTL(t, True) #re-open blue mot aom after switch off 

stop(t+GLOBALS['stop_buffering_time'])