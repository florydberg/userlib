########## SUB ROUTINES #######################
# by Andrea for Sr FloRydberg Group           #
# register of actions for Labscript Ruotines  #
# last edited 06/03/2024                      # 
###############################################
from user_devices.mogdevice import MOGDevice
import runmanager.remote
import h5py
from labscript_utils import import_or_reload
import_or_reload('labscriptlib.Sr.connection_table')
from labscriptlib.Sr.connection_table import *

if True: #init of globals and times
    if True: # Time Constants
        t=0
        dt=main_board.time_step # 1 us
        usec=dt
        us=usec
        msec=1000*dt
        ms=msec
        sec=1000000*dt
        s=sec
        min=60*sec
    settings_path='F:\\Experiments\\Sr\\SrParameters.h5'
    units={}
    for globals_group  in runmanager.get_grouplist(settings_path):
        for global_name in runmanager.get_globalslist(settings_path, globals_group):
            with h5py.File(settings_path,'r') as shot_h5py: global_units =  shot_h5py["globals"][globals_group]["units"].attrs[global_name]
            if global_units=='us': #base unit for time
                g_unit=usec
            elif global_units=='ms':
                g_unit=msec
            elif global_units=='s':
                g_unit=sec
            elif global_units=='Hz':#base unit for frequency
                g_unit=1
            elif global_units=='kHz':
                e_unit=1e3
            elif global_units=='MHz':
                g_unit=1e6
            else:
                g_unit=1
            units[str(global_name)]=g_unit
    GLOBALS={}
    for i in runmanager.remote.get_globals():
        GLOBALS[str(i)]=eval(i)*units[str(i)]

if True: #Envelope of ttl and analog

    def TABLE_MODE_ON(channel_name, tt): 
        
        trigger_name = channel_name+'_trigger'
        channel_trigger = globals().get(trigger_name)

        channel_trigger.go_high(tt)
        channel_trigger.go_low(tt+dt)

    def TABLE_MODE_OFF(channel_name, tt): 

        channel = globals().get(channel_name)
        channel.DDS.setamp(tt, 0e2)
        channel.DDS.setfreq(tt, 10e3)
    
        trigger_name = channel_name+'_trigger'
        channel_trigger = globals().get(trigger_name)

        channel_trigger.go_high(tt)
        channel_trigger.go_low(tt+dt)

    def NEW_TABLE_LINE(channel_name, tt, frequency, amplitude):

        channel = globals().get(channel_name)
        channel.DDS.setamp(tt, amplitude*1e2)
        channel.DDS.setfreq(tt, frequency*1e3)

        trigger_name = channel_name+'_trigger'
        channel_trigger = globals().get(trigger_name)

        channel_trigger.go_high(tt)
        channel_trigger.go_low(tt+dt)

    def MOT_Blue2D_AOM_TTL(tt, control=True):
        if control:
            dueD_MOT_gate.go_high(tt) #QRF MOGLABS
        else:
            dueD_MOT_gate.go_low(tt)
    
    def MOT_Blue3D_AOM_TTL(tt, control=True):
        if control:
            treD_MOT_gate.go_high(tt) #QRF MOGLABS
        else:
            treD_MOT_gate.go_low(tt)
    
    def MOT_Blue3D_AOM_freq(tt, value):
        return
    
    def MOT_Blue3D_AOM_power(tt, value):
        return

    def MOT_Red3D_AOM_TTL(tt, control=True):
        if control:
            RedMOT_gate.go_high(tt)  #QRF MOGLABS
        else:
            RedMOT_gate.go_low(tt) 

    def MOT_Red3D_Switch_TTL(tt, control=True):
        if control:
            Red_commonSwitch.go_high(tt) #RF switch
        else:
            Red_commonSwitch.go_low(tt) 

    def MOT_Red3D_multiFrq_TTL(tt, control=True):
        if control:
            Red_multiFrq.go_high(tt) 
        else:
            Red_multiFrq.go_low(tt) 

    def MOT_Red3D_singleFrq_TTL(tt, control=True):
        if control:
            Red_singleFrq.go_high(tt)
        else:
            Red_singleFrq.go_low(tt) 

    def Sisyphus_AOM_TTL(tt, control=True):
        if control:
            Sisyphus_gate.go_high(tt)
        else:
            Sisyphus_gate.go_low(tt)

    def BlueImaging_AOM_TTL(tt, control=True):
        if control:
            ImagingBeam_gate.go_high(tt)
        else:
            ImagingBeam_gate.go_low(tt)

    def BlueImagingTweez_AOM_TTL(tt, control=True):
        if control:
            ImagingTweezBeam_gate.go_high(tt)
        else:
            ImagingTweezBeam_gate.go_low(tt)        

    def Twizzi_Switch_TTL(tt, control=True):
        if control:
            Tweezer_gate.go_high(tt)
        else:
            Tweezer_gate.go_low(tt)

    def MOT_Blue3D_Shutter_TTL(tt, control=True):
        if control:
            Shutter_Blue.go_high(tt)
        else:
            Shutter_Blue.go_low(tt)

    def COILSmain_SwitchON_TTL(tt, control=True):
        if control:
            IGBT_close.go_high(tt)
        else:
            IGBT_close.go_low(tt)

    def COILSmain_Config(tt, type):
        if type=='H':
            return
        elif type=='AH':
            return
        else:
            print('Value not allowed.')

    def COILSmain_Current(tt, value=0):
        BigCoilsI.constant(tt, abs(value))

    def COILSmain_Voltage(tt, value=0):
        BigCoilsV.constant(tt, abs(value))

    def COILScompX_Current(tt, value=0):
        CompCoilsI_X.constant(tt, abs(value))

    def COILScompY_Current(tt, value=0):
        CompCoilsI_Y.constant(tt, abs(value))

    def COILScompZ_Current(tt, value=0):
        CompCoilsI_Z.constant(tt, abs(value))

    def COILScomp_SwitchON_TTL(tt, control=True):
        if control:
            coilsMosfet.go_high(tt+dt)
        else:
            coilsMosfet.go_low(tt+dt)

    def Current_span(coils, tt, Final_V, Initial_V):
        n_step=round(Final_V-Initial_V/0.001)
        if n_step>0:
            for i in range(0,n_step):
                tt+=100*usec
                coils(tt, GLOBALS['Z_Coils_Current']+i*0.001)
                return tt
        else:
            step_n=-n_step
            for i in range(0,step_n):
                tt+=100*usec
                coils(tt, GLOBALS['Z_Coils_Current']-i*0.001)  
                return tt 
        
def BlueMot_load(tt, load_time):
    tt+=dt        
    COILSmain_SwitchON_TTL(tt, True)
    tt+=dt
    MOT_Blue3D_Shutter_TTL(tt, False)
    tt+=2*msec
    MOT_Blue3D_AOM_TTL(tt, False)

    COILSmain_Current(tt, GLOBALS['coils_current_cntrl'])
    tt+=dt
    COILSmain_Voltage(tt, 5)
    tt+=dt

    MOT_Blue2D_AOM_TTL(tt, True)
    MOT_Blue3D_AOM_TTL(tt, True)
    tt+=load_time
    return tt
   
def BlueMot_load_Table(tt, load_time):
    tt+=dt        
    COILSmain_SwitchON_TTL(tt, True)
    tt+=dt
    MOT_Blue3D_Shutter_TTL(tt, False)
    tt+=2*msec
    # TABLE_MODE_OFF('treD_MOT', tt)
    # tt+=20*usec

    COILSmain_Current(tt, GLOBALS['coils_current_cntrl'])
    tt+=dt
    COILSmain_Voltage(tt, 5)
    tt+=dt

    MOT_Blue2D_AOM_TTL(tt, True)

    NEW_TABLE_LINE('treD_MOT', tt, GLOBALS['treD_MOT_Frq']/1e6, GLOBALS['treD_MOT_Pow'])

    tt+=load_time
    return tt

def BlueMot_off_Table(tt):
    MOT_Blue2D_AOM_TTL(tt-GLOBALS['TwoD_DELAY']+dt, False)
    TABLE_MODE_OFF('treD_MOT', tt)
    tt+=2*usec
    tt+=dt
    MOT_Blue3D_Shutter_TTL(tt-1*msec, True)

    tt+=dt
    COILSmain_Current(tt,0)
    tt+=1*usec
    COILSmain_SwitchON_TTL(tt, False)
    tt+=dt

    return tt

def BlueMot_off(tt):
    MOT_Blue2D_AOM_TTL(tt-GLOBALS['TwoD_DELAY']+dt, False)
    MOT_Blue3D_AOM_TTL(tt, False)
    tt+=dt
    MOT_Blue3D_Shutter_TTL(tt-1*msec, True)

    tt+=dt
    COILSmain_Current(tt,0)
    tt+=1*usec
    COILSmain_SwitchON_TTL(tt, False)
    tt+=dt

    return tt

def BlueMot(tt, loading_time):
    tt=BlueMot_load(tt, loading_time)
    tt=BlueMot_off(tt)
    return tt

def BlueMot_Table(tt, loading_time):
    tt=BlueMot_load_Table(tt, loading_time)
    tt=BlueMot_off_Table(tt)
    return tt

def BlueMOT_molass(tt, loading_time, T_BlueMolass):
    #MOT
    tt=BlueMot_load(tt, loading_time)
    MOT_Blue2D_AOM_TTL(tt-GLOBALS['TwoD_DELAY']+dt, False)

    tt+=dt
    COILSmain_Current(tt,0)
    tt+=1*usec
    COILSmain_SwitchON_TTL(tt, False)
    tt+=dt

    #MOLASS
    tt+=T_BlueMolass

    MOT_Blue3D_AOM_TTL(tt, False)
    tt+=dt
    COILSmain_SwitchON_TTL(tt-2*msec, True)
    MOT_Blue3D_AOM_TTL(tt+20*msec, False)

    return tt

def RedMot_on(tt):
    tt+=dt
    MOT_Red3D_AOM_TTL(tt, True)
    tt+=dt
    return tt

def RedMot_off(tt):
    tt+=dt
    MOT_Red3D_AOM_TTL(tt, False)
    tt+=dt
    return tt

def RedMot(tt, duration_wait):
    tt=RedMot_on(tt)
    tt=RedMot_off(tt+duration_wait)
    return tt

def RedMot_on_multifrq(tt):
    tt+=dt
    MOT_Red3D_multiFrq_TTL(tt, True) 
    tt+=dt
    return tt

def RedMot_off_multifrq(tt):
    tt+=dt
    MOT_Red3D_multiFrq_TTL(tt, False) 
    tt+=dt
    return tt

def RedMot_multifrq(tt, duration_wait):
    
    MOT_Red3D_Switch_TTL(tt, True)
    tt+=dt
    tt=RedMot_on_multifrq(tt)
    tt=RedMot_off_multifrq(tt+duration_wait)
    MOT_Red3D_Switch_TTL(tt, False)
    
    return tt

def Red_Mot_Luca(tt, red_duration, blue_duration, shield):

    MOT_Red3D_Switch_TTL(tt, True)      #Global rf switch
    tt+=dt

    if shield:
        MOT_Red3D_AOM_TTL(tt, True)     
        tt+=dt
        MOT_Red3D_multiFrq_TTL(tt, False) 
        MOT_Red3D_singleFrq_TTL(tt, True) 

    tt=BlueMot_load(tt, blue_duration)       #Blue mot loading

    MOT_Blue2D_AOM_TTL(tt-GLOBALS['TwoD_DELAY']+dt, False)
    MOT_Blue3D_AOM_TTL(tt, False)
    tt+=dt
    MOT_Blue3D_Shutter_TTL(tt-1*msec, True)

 ##### RED MOT SECTION

    MOT_Red3D_AOM_TTL(tt, False)        #Luca moved this part here to turn on the comb even during the switching off
    tt+=dt
    MOT_Red3D_singleFrq_TTL(tt, False) 
    tt+=dt
    MOT_Red3D_multiFrq_TTL(tt, True)

    tt+=red_duration

    COILSmain_Current(tt, 0)
    tt+=1*usec
    COILSmain_SwitchON_TTL(tt, False)
    tt+=dt

    MOT_Red3D_Switch_TTL(tt, False)       #Luca commented this part to use the4 function in RED_MOT_Salvi
    MOT_Red3D_multiFrq_TTL(tt, False)          

    return tt

def RedBroad_Mot(tt, red_duration, blue_duration, shield, shieldMulti):

    MOT_Red3D_Switch_TTL(tt, True)      #Global rf switch
    tt+=dt

    if shield:
        MOT_Red3D_AOM_TTL(tt, True)     
        tt+=dt
        MOT_Red3D_multiFrq_TTL(tt, False) 
        MOT_Red3D_singleFrq_TTL(tt, True) 

    if shieldMulti:
        MOT_Red3D_AOM_TTL(tt, False)     
        tt+=dt
        MOT_Red3D_multiFrq_TTL(tt, True) 
        MOT_Red3D_singleFrq_TTL(tt, False) 

    tt=BlueMot(tt, blue_duration)       #Blue mot loading

 ##### RED MOT SECTION

    MOT_Red3D_AOM_TTL(tt, False)        #Luca moved this part here to turn on the comb even during the switching off
    tt+=dt
    MOT_Red3D_singleFrq_TTL(tt, False) 
    tt+=dt
    MOT_Red3D_multiFrq_TTL(tt, True)

    #IGBT_close.go_high(tt)
    tt+=400*usec
    IGBT_close.go_high(tt)
    tt+=dt
    COILSmain_Current(tt, GLOBALS['coils_current_ctrl_red'])          #Turn on the COILSmain at 10 A, roughly 5 G/cm
    tt+=dt
    COILSmain_Voltage(tt, 0.8)
    tt+=dt

    ## tt+=300*us
    # MOT_Red3D_AOM_TTL(tt, False)
    # tt+=dt
    # MOT_Red3D_singleFrq_TTL(tt, False) 
    # tt+=dt
    # MOT_Red3D_multiFrq_TTL(tt, True)

    tt+=red_duration

    tt+=dt
    COILSmain_Current(tt, 0)
    tt+=1*usec
    COILSmain_SwitchON_TTL(tt, False)
    tt+=dt

    MOT_Red3D_Switch_TTL(tt, False)       #Luca commented this part to use the4 function in RED_MOT_Salvi
    MOT_Red3D_multiFrq_TTL(tt, False)          

    return tt

def RedBroad_Mot_Final(tt, red_duration, blue_duration, shield, shieldMulti):

    MOT_Red3D_Switch_TTL(tt, True)      #Global rf switch
    tt+=dt

    if shield:
        MOT_Red3D_AOM_TTL(tt, True)     
        tt+=dt
        MOT_Red3D_multiFrq_TTL(tt, False) 
        MOT_Red3D_singleFrq_TTL(tt, True) 

    if shieldMulti:
        MOT_Red3D_AOM_TTL(tt, False)     
        tt+=dt
        MOT_Red3D_multiFrq_TTL(tt, True) 
        MOT_Red3D_singleFrq_TTL(tt, False) 

    tt=BlueMot_load(tt, blue_duration)

    MOT_Blue2D_AOM_TTL(tt-GLOBALS['TwoD_DELAY']+dt, False)
    MOT_Blue3D_AOM_TTL(tt, False)
    tt+=dt
    MOT_Blue3D_Shutter_TTL(tt-1*msec, True)

    tt+=dt
    COILSmain_Voltage(tt, 0)
    tt+=dt
    COILSmain_Current(tt,0)
    tt+=1*usec
    COILSmain_SwitchON_TTL(tt, False)
    tt+=dt

    # tt+=dt
    # COILSmain_Current(tt,GLOBALS['coils_current_ctrl_red'])
    tt+=dt

  ##### RED MOT SECTION

    MOT_Red3D_AOM_TTL(tt, False)        #Luca moved this part here to turn on the comb even during the switching off
    tt+=dt
    MOT_Red3D_singleFrq_TTL(tt, False) 
    tt+=dt
    MOT_Red3D_multiFrq_TTL(tt, True)

    #IGBT_close.go_high(tt)
    tt+=300*usec
    IGBT_close.go_high(tt)
    tt+=dt
    COILSmain_Voltage(tt, 0.4)
    tt+=dt
    COILSmain_Current(tt, GLOBALS['coils_current_ctrl_red'])          #Turn on the COILSmain at 10 A, roughly 5 G/cm
    tt+=dt


    ## tt+=300*us
    # MOT_Red3D_AOM_TTL(tt, False)
    # tt+=dt
    # MOT_Red3D_singleFrq_TTL(tt, False) 
    # tt+=dt
    # MOT_Red3D_multiFrq_TTL(tt, True)

    tt+=red_duration

    tt+=dt
    COILSmain_Current(tt, 0)
    tt+=1*usec
    COILSmain_SwitchON_TTL(tt, False)
    tt+=dt

    MOT_Red3D_Switch_TTL(tt, False)       #Luca commented this part to use the4 function in RED_MOT_Salvi
    MOT_Red3D_multiFrq_TTL(tt, False)          

    return tt

def RedBroad_Mot_Test(tt, red_duration, blue_duration, shield, shieldMulti):

    MOT_Red3D_Switch_TTL(tt, True)      #Global rf switch
    tt+=dt

    if shield:
        MOT_Red3D_AOM_TTL(tt, True)     
        tt+=dt
        MOT_Red3D_multiFrq_TTL(tt, False) 
        MOT_Red3D_singleFrq_TTL(tt, True) 

    if shieldMulti:
        MOT_Red3D_AOM_TTL(tt, False)     
        tt+=dt
        MOT_Red3D_multiFrq_TTL(tt, True) 
        MOT_Red3D_singleFrq_TTL(tt, False) 

    tt=BlueMot_load(tt, blue_duration)

    MOT_Blue2D_AOM_TTL(tt-GLOBALS['TwoD_DELAY']+dt, False)
    MOT_Blue3D_AOM_TTL(tt, False)
    tt+=dt
    MOT_Blue3D_Shutter_TTL(tt-1*msec, True)

    # treD_MOT.DDS.setamp(tt, GLOBALS['treD_MOT_Pow']*1e2/10)

    tt+=dt
    COILSmain_Voltage(tt, 0)
    tt+=dt
    COILSmain_Current(tt,0)
    tt+=1*usec
    COILSmain_SwitchON_TTL(tt, False)
    tt+=dt

    # tt+=dt
    # COILSmain_Current(tt,GLOBALS['coils_current_ctrl_red'])
    tt+=dt

 ##### RED MOT SECTION

    MOT_Red3D_AOM_TTL(tt, False)        #Luca moved this part here to turn on the comb even during the switching off
    tt+=dt
    MOT_Red3D_singleFrq_TTL(tt, False) 
    tt+=dt
    MOT_Red3D_multiFrq_TTL(tt, True)

    tt+=300*usec
    COILSmain_SwitchON_TTL(tt, True)
    # IGBT_close.go_high(tt)
    tt+=dt
    COILSmain_Voltage(tt, 0.4)
    tt+=dt
    COILSmain_Current(tt, GLOBALS['coils_current_ctrl_red'])          #Turn on the COILSmain at 10 A, roughly 5 G/cm


    ## tt+=300*us
    # MOT_Red3D_AOM_TTL(tt, False)
    # tt+=dt
    # MOT_Red3D_singleFrq_TTL(tt, False) 
    # tt+=dt
    # MOT_Red3D_multiFrq_TTL(tt, True)

    tt+=red_duration/2

    # COILSmain_Current(tt, GLOBALS['coils_current_ctrl_red']*0.2)
    # tt+=red_duration/2
    # COILSmain_Current(tt, GLOBALS['coils_current_ctrl_red']*0.4)          #Increases the gradient gradually
    # tt+=red_duration/8
    # COILSmain_Current(tt, GLOBALS['coils_current_ctrl_red']*0.6)          
    # tt+=red_duration/8
    # COILSmain_Current(tt, GLOBALS['coils_current_ctrl_red']*0.8)          
    # tt+=red_duration/8
    # COILSmain_Current(tt, GLOBALS['coils_current_ctrl_red']*1)          
    # tt+=red_duration/8

    # COILScompZ_Current(tt, GLOBALS['coils_current_ctrl_red']*1.00001)
    # tt+=red_duration/4
    # COILScompZ_Current(tt, GLOBALS['coils_current_ctrl_red']*1.00002)
    # tt+=red_duration/4
    # COILScompZ_Current(tt, GLOBALS['coils_current_ctrl_red']*1.15)
    # tt+=red_duration/4
    # COILScompZ_Current(tt, GLOBALS['coils_current_ctrl_red']*1.2)
    tt+=red_duration/4

    tt+=dt

    MOT_Red3D_multiFrq_TTL(tt, False)
    tt+=dt
    MOT_Red3D_AOM_TTL(tt, True)        #Single frequency mot
    tt+=dt
    MOT_Red3D_singleFrq_TTL(tt, True)     
    tt+=red_duration/12


    tt+=dt
    COILSmain_Current(tt, 0)
    tt+=1*usec
    COILSmain_SwitchON_TTL(tt, False)
    tt+=dt

    MOT_Red3D_Switch_TTL(tt, False)       #Luca commented this part to use the4 function in RED_MOT_Salvi
    MOT_Red3D_singleFrq_TTL(tt, False)
    # MOT_Red3D_multiFrq_TTL(tt, False)          


    return tt

def RedMot_single(tt, red_duration, blue_duration, shield, shieldMulti):

    MOT_Red3D_Switch_TTL(tt, True)      #Global rf switch
    tt+=dt

    if shield:
        MOT_Red3D_AOM_TTL(tt, True)     
        tt+=dt
        MOT_Red3D_multiFrq_TTL(tt, False) 
        MOT_Red3D_singleFrq_TTL(tt, True) 

    if shieldMulti:
        MOT_Red3D_AOM_TTL(tt, False)     
        tt+=dt
        MOT_Red3D_multiFrq_TTL(tt, True) 
        MOT_Red3D_singleFrq_TTL(tt, False) 

    tt=BlueMot_load(tt, blue_duration)

    MOT_Blue2D_AOM_TTL(tt-GLOBALS['TwoD_DELAY']+dt, False)
    MOT_Blue3D_AOM_TTL(tt, False)
    tt+=dt
    MOT_Blue3D_Shutter_TTL(tt-1*msec, True)

    # treD_MOT.DDS.setamp(tt, GLOBALS['treD_MOT_Pow']*1e2/10)

    tt+=dt
    COILSmain_Voltage(tt, 0)
    tt+=dt
    COILSmain_Current(tt,0)
    tt+=1*usec
    COILSmain_SwitchON_TTL(tt, False)
    tt+=dt

    # tt+=dt
    # COILSmain_Current(tt,GLOBALS['coils_current_ctrl_red'])
    tt+=dt

 ##### RED MOT SECTION

    MOT_Red3D_AOM_TTL(tt, False)        #Luca moved this part here to turn on the comb even during the switching off
    tt+=dt
    MOT_Red3D_singleFrq_TTL(tt, False) 
    tt+=dt
    MOT_Red3D_multiFrq_TTL(tt, True)

    tt+=300*usec
    COILSmain_SwitchON_TTL(tt, True)
    # IGBT_close.go_high(tt)
    tt+=dt
    COILSmain_Voltage(tt, 0.4)
    tt+=dt
    COILSmain_Current(tt, GLOBALS['coils_current_ctrl_red'])          #Turn on the COILSmain at 10 A, roughly 5 G/cm


    ## tt+=300*us
    # MOT_Red3D_AOM_TTL(tt, False)
    # tt+=dt
    # MOT_Red3D_singleFrq_TTL(tt, False) 
    # tt+=dt
    # MOT_Red3D_multiFrq_TTL(tt, True)

    tt+=red_duration/2

    # COILSmain_Current(tt, GLOBALS['coils_current_ctrl_red']*0.2)
    # tt+=red_duration/2
    # COILSmain_Current(tt, GLOBALS['coils_current_ctrl_red']*0.4)          #Increases the gradient gradually
    # tt+=red_duration/8
    # COILSmain_Current(tt, GLOBALS['coils_current_ctrl_red']*0.6)          
    # tt+=red_duration/8
    # COILSmain_Current(tt, GLOBALS['coils_current_ctrl_red']*0.8)          
    # tt+=red_duration/8
    # COILSmain_Current(tt, GLOBALS['coils_current_ctrl_red']*1)          
    # tt+=red_duration/8

    # COILScompZ_Current(tt, GLOBALS['coils_current_ctrl_red']*1.00001)
    # tt+=red_duration/4
    # COILScompZ_Current(tt, GLOBALS['coils_current_ctrl_red']*1.00002)
    # tt+=red_duration/4
    # COILScompZ_Current(tt, GLOBALS['coils_current_ctrl_red']*1.15)
    # tt+=red_duration/4
    # COILScompZ_Current(tt, GLOBALS['coils_current_ctrl_red']*1.2)
    tt+=red_duration/4

    tt+=dt

    MOT_Red3D_multiFrq_TTL(tt, False)
    tt+=dt
    MOT_Red3D_AOM_TTL(tt, True)        #Single frequency mot
    tt+=dt
    MOT_Red3D_singleFrq_TTL(tt, True)     
    tt+=red_duration/4


    tt+=dt
    COILSmain_Current(tt, 0)
    tt+=1*usec
    COILSmain_SwitchON_TTL(tt, False)
    tt+=dt

    MOT_Red3D_Switch_TTL(tt, False)       #Luca commented this part to use the4 function in RED_MOT_Salvi
    MOT_Red3D_singleFrq_TTL(tt, False)
    # MOT_Red3D_multiFrq_TTL(tt, False)          


    return tt

def RedMot_singleTable(tt, red_duration, blue_duration, shield, shieldMulti):

    MOT_Red3D_Switch_TTL(tt, True)      #Global rf switch
    tt+=dt

    if shield:
        MOT_Red3D_AOM_TTL(tt, True)     
        tt+=dt
        MOT_Red3D_multiFrq_TTL(tt, False) 
        MOT_Red3D_singleFrq_TTL(tt, True) 

    if shieldMulti:
        MOT_Red3D_AOM_TTL(tt, False)     
        tt+=dt
        MOT_Red3D_multiFrq_TTL(tt, True) 
        MOT_Red3D_singleFrq_TTL(tt, False) 

    tt=BlueMot_load(tt, blue_duration)

    MOT_Blue2D_AOM_TTL(tt-GLOBALS['TwoD_DELAY']+dt, False)
    MOT_Blue3D_AOM_TTL(tt, False)
    tt+=dt
    MOT_Blue3D_Shutter_TTL(tt-1*msec, True)

    # treD_MOT.DDS.setamp(tt, GLOBALS['treD_MOT_Pow']*1e2/10)

    tt+=dt
    COILSmain_Voltage(tt, 0)
    tt+=dt
    COILSmain_Current(tt,0)
    tt+=1*usec
    COILSmain_SwitchON_TTL(tt, False)
    tt+=dt

    # tt+=dt
    # COILSmain_Current(tt,GLOBALS['coils_current_ctrl_red'])
    tt+=dt

 ##### RED MOT SECTION

    MOT_Red3D_AOM_TTL(tt, False)        #Luca moved this part here to turn on the comb even during the switching off
    tt+=dt
    MOT_Red3D_singleFrq_TTL(tt, False) 
    tt+=dt
    MOT_Red3D_multiFrq_TTL(tt, True)

    tt+=300*usec
    COILSmain_SwitchON_TTL(tt, True)
    # IGBT_close.go_high(tt)
    tt+=dt
    COILSmain_Voltage(tt, 0.4)
    tt+=dt
    COILSmain_Current(tt, GLOBALS['coils_current_ctrl_red'])          #Turn on the COILSmain at 10 A, roughly 5 G/cm


    tt+=red_duration

    tt+=dt

    MOT_Red3D_multiFrq_TTL(tt, False)
    tt+=dt
    # MOT_Red3D_AOM_TTL(tt, True)        #Single frequency mot
    NEW_TABLE_LINE('RedMOT', tt, GLOBALS['Red_MOT_Frq']/1e6, GLOBALS['Red_MOT_Pow'])
    tt+=3*dt
    MOT_Red3D_singleFrq_TTL(tt, True)     


    tt+=red_duration/4

    # COILSmain_Current(tt, GLOBALS['coils_current_ctrl_red']*1.2)  
    # tt+=dt
    # NEW_TABLE_LINE('RedMOT', tt, GLOBALS['Red_MOT_Frq']/1e6, GLOBALS['Red_MOT_Pow'])
    # NEW_TABLE_LINE('RedMOT', tt, 75.455, 21.5)
    # tt+=3*dt
    
    # tt+=3*dt

    # tt+=red_duration

    # NEW_TABLE_LINE('RedMOT', tt, 75.455, 20)
    # COILSmain_Current(tt, GLOBALS['coils_current_ctrl_red'])  
    # tt+=3*dt

    # tt+=red_duration/8

    # NEW_TABLE_LINE('RedMOT', tt, 75.455, 18.5)
    # COILSmain_Current(tt, GLOBALS['coils_current_ctrl_red'])  
    # tt+=3*dt

    # tt+=red_duration/8
    # tt+=3*dt
    COILSmain_Current(tt, 0)
    tt+=1*usec
    COILSmain_SwitchON_TTL(tt, False)
    tt+=dt

    MOT_Red3D_Switch_TTL(tt, False)       
    MOT_Red3D_singleFrq_TTL(tt, False)
        
    return tt

def RedBroad_Mot_Table(tt, red_duration, blue_duration, shield, shieldMulti):

    MOT_Red3D_Switch_TTL(tt, True)      #Global rf switch
    tt+=5*msec

    if shield:
        MOT_Red3D_AOM_TTL(tt, True)     
        tt+=dt
        MOT_Red3D_multiFrq_TTL(tt, False) 
        MOT_Red3D_singleFrq_TTL(tt, True) 
    elif shieldMulti:
        MOT_Red3D_AOM_TTL(tt, False)     
        tt+=dt
        MOT_Red3D_multiFrq_TTL(tt, True) 
        MOT_Red3D_singleFrq_TTL(tt, False) 


    tt=BlueMot_load_Table(tt, blue_duration)

    ### Blue MOT OFF
    MOT_Blue2D_AOM_TTL(tt-GLOBALS['TwoD_DELAY']+dt, False)
    TABLE_MODE_OFF('treD_MOT',tt) 
    tt+=2*usec
    tt+=dt
    MOT_Blue3D_Shutter_TTL(tt-1*msec, True)
    
    tt+=dt
    COILSmain_Voltage(tt, 0)
    tt+=dt
    COILSmain_Current(tt,0)
    tt+=1*usec
    COILSmain_SwitchON_TTL(tt, False)
    tt+=dt


 #### RED MOT SECTION
 
    MOT_Red3D_AOM_TTL(tt, False)        #Luca moved this part here to turn on the comb even during the switching off
    tt+=dt
    MOT_Red3D_singleFrq_TTL(tt, False) 
    tt+=dt
    MOT_Red3D_multiFrq_TTL(tt, True)

    tt+=300*usec
    COILSmain_SwitchON_TTL(tt, True)
    # IGBT_close.go_high(tt)
    tt+=dt
    COILSmain_Voltage(tt, 0.4)
    tt+=dt
    COILSmain_Current(tt, GLOBALS['coils_current_ctrl_red'])          #Turn on the COILSmain at 10 A, roughly 5 G/cm


    tt+=red_duration/2

    tt+=red_duration/4

    tt+=dt

    MOT_Red3D_multiFrq_TTL(tt, False)
    tt+=dt
    MOT_Red3D_AOM_TTL(tt, True)        #Single frequency mot
    tt+=dt
    MOT_Red3D_singleFrq_TTL(tt, True)     
    tt+=red_duration/4


    tt+=dt
    COILSmain_Current(tt, 0)
    tt+=1*usec
    COILSmain_SwitchON_TTL(tt, False)
    tt+=dt

    MOT_Red3D_Switch_TTL(tt, False)       #Luca commented this part to use the4 function in RED_MOT_Salvi
    MOT_Red3D_singleFrq_TTL(tt, False)
    # MOT_Red3D_multiFrq_TTL(tt, False)          


    return tt

def take_absorbImaging(tt, beam_duration):
    trigger_delay=100*usec+5*usec #100 for camera activation + 5 as safety buffer
    Basler_Camera_abs_readout=4*120*msec # was at 120ms with small ROI, when enlarged changed to 200ms, still had issues capturing, changed to 480 and no issue

    pokemon16.go_high(tt-trigger_delay-10*usec)
    pokemon16.go_low(tt-trigger_delay-10*usec+1*ms)
    BlueImaging_AOM_TTL(tt, True)
    BlueImaging_AOM_TTL(tt+beam_duration, False)
    tt+=Basler_Camera_abs.expose(tt-trigger_delay,'Atoms', frametype='tiff')
    # Basler_Camera_abs_trigger.go_high(tt-trigger_delay-5*usec)
    # Basler_Camera_abs_trigger.go_low(tt-trigger_delay+1*msec)
    
    tt+=Basler_Camera_abs_readout 

    BlueImaging_AOM_TTL(tt, True)
    BlueImaging_AOM_TTL(tt+beam_duration, False)
    tt+=Basler_Camera_abs.expose(tt-trigger_delay,'Probe', frametype='tiff')
    # Basler_Camera_abs_trigger.go_high(tt-trigger_delay-5*usec)
    # Basler_Camera_abs_trigger.go_low(tt-trigger_delay+1*msec)

    tt+=Basler_Camera_abs_readout 

    Basler_Camera_abs.expose(tt-trigger_delay,'Background', frametype='tiff')
    # Basler_Camera_abs_trigger.go_high(tt-trigger_delay-5*usec)
    # Basler_Camera_abs_trigger.go_low(tt-trigger_delay+1*msec)

    tt+=Basler_Camera_abs_readout 

    return tt

def take_absorbImaging_test(tt, beam_duration):
    trigger_delay=100*usec+5*usec #100 for camera activation + 5 as safety buffer
    Basler_Camera_abs_readout=120*msec # was at 120ms, changed to 200ms, still had issues capturing, changed to 300 and no issue

    MOT_Blue2D_AOM_TTL(tt, True)
    MOT_Blue2D_AOM_TTL(tt+beam_duration, False)
    tt+=Basler_Camera_abs.expose(tt-trigger_delay,'Atoms', frametype='tiff')
    
    tt+=4*Basler_Camera_abs_readout 

    MOT_Blue2D_AOM_TTL(tt, True)
    MOT_Blue2D_AOM_TTL(tt+beam_duration, False)
    tt+=Basler_Camera_abs.expose(tt-trigger_delay,'Probe', frametype='tiff')

    tt+=4*Basler_Camera_abs_readout 

    Basler_Camera_abs.expose(tt-trigger_delay,'Background', frametype='tiff')

    tt+=10*Basler_Camera_abs_readout 

    return tt

def do_Twizzi(tt, Tweezer_duration):
    Twizzi_Switch_TTL(tt, True)
    tt+=Tweezer_duration
    Twizzi_Switch_TTL(tt, False)
    return tt
    
def take_fluoImaging_Andor(tt, name):

    BlueImaging_AOM_TTL(tt+10*usec, True)
    tt+=Andor_Camera.expose(tt, str(name), frametype='tiff') 
    BlueImaging_AOM_TTL(tt, False)
    return tt

def take_fluoImaging_Basler(tt, name):
    trigger_delay=100*usec+5*usec
    tt+=Basler_Camera_abs.expose(tt-trigger_delay,name, frametype='tiff')
    return tt

def set_MOGLABS_ready(tt):
    G_Imaging_Frq=GLOBALS['Imaging_Frq']/1e6
    G_dueD_MOT_Frq=GLOBALS['dueD_MOT_Frq']/1e6
    G_treD_MOT_Frq=GLOBALS['treD_MOT_Frq']/1e6
    G_Red_MOT_Frq=GLOBALS['Red_MOT_Frq']/1e6
    G_ImagingTweez_Frq=GLOBALS['ImagingTweez_Frq']/1e6
    G_Sisyphus_Frq=GLOBALS['Sisyphus_Frq']/1e6
        
    G_Imaging_Pow=GLOBALS['Imaging_Pow']
    G_treD_MOT_Pow=GLOBALS['treD_MOT_Pow']
    G_Red_MOT_Pow=GLOBALS['Red_MOT_Pow']
    G_ImagingTweez_Pow=GLOBALS['ImagingTweez_Pow']
    G_dueD_MOT_Pow=GLOBALS['dueD_MOT_Pow']    
    G_Sisyphus_Pow=GLOBALS['Sisyphus_Pow']

    # RedMOT.DDS.setfreq(tt, G_Red_MOT_Frq*1e3)  ##################### VERY VERY  BAD THINGS TO CIRCUMVENT DRIVER BUG  TODO: FIX removing 1e3or2 ask Andre #################
    # RedMOT.DDS.setamp(tt, G_Red_MOT_Pow*1e2)

    ImagingBeam.DDS.setfreq(tt, G_Imaging_Frq*1e3)
    ImagingBeam.DDS.setamp(tt, G_Imaging_Pow*1e2)

    dueD_MOT.DDS.setfreq(tt, G_dueD_MOT_Frq*1e3)
    dueD_MOT.DDS.setamp(tt, G_dueD_MOT_Pow*1e2)

    treD_MOT.DDS.setfreq(tt, G_treD_MOT_Frq*1e3)
    treD_MOT.DDS.setamp(tt, G_treD_MOT_Pow*1e2)

    ImagingTweezBeam.DDS.setfreq(tt, G_ImagingTweez_Frq*1e3)
    ImagingTweezBeam.DDS.setamp(tt, G_ImagingTweez_Pow*1e2)

    Sisyphus.DDS.setfreq(tt, G_Sisyphus_Frq*1e3)
    Sisyphus.DDS.setamp(tt, G_Sisyphus_Pow*1e2)

def set_CompCoils(tt):
    COILScomp_SwitchON_TTL(t+dt, True)
    tt+=5*usec
    COILScompX_Current(tt, abs(GLOBALS['X_Coils_Current']))
    tt+=dt
    COILScompY_Current(tt, abs(GLOBALS['Y_Coils_Current']))
    tt+=dt
    COILScompZ_Current(tt, abs(GLOBALS['Z_Coils_Current']))
    tt+=dt
    return tt
    
def setoff_CompCoils(tt):
    COILScomp_SwitchON_TTL(t, False)
    tt+=5*usec
    CompCoilsI_X.constant(tt, 0)
    tt+=dt
    CompCoilsI_Y.constant(tt, 0)
    tt+=dt
    CompCoilsI_Z.constant(tt, 0)
    tt+=dt
    return tt 
   
def fluo_resonant_Blue(tt):
    BlueImaging_AOM_TTL(tt+10*usec, True)
    exposure_time=10000*usec

    # tt-=100*msec ##############################################
    Andor_Camera_trigger.go_high(tt)
    # tt+=Andor_Camera.expose(tt+dt,'Fluo0', frametype='tiff') 
    tt+=10*usec   
    Andor_Camera_trigger.go_low(tt)
    # tt+=100*msec ##############################################

    tt+=exposure_time

    BlueImaging_AOM_TTL(tt, False)

    return tt

def fluo_detuned_Blue(tt):
    BlueImagingTweez_AOM_TTL(tt+10*usec, True)
    exposure_time=10000*usec

    # tt-=100*msec ##############################################
    Andor_Camera_trigger.go_high(tt)
    # tt+=Andor_Camera.expose(tt+dt,'Fluo0', frametype='tiff') 
    tt+=10*usec   
    Andor_Camera_trigger.go_low(tt)
    # tt+=100*msec ##############################################

    tt+=exposure_time

    BlueImagingTweez_AOM_TTL(tt, False)

    return tt