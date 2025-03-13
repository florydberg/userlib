#___________________________________________________________________________________#
from labscript import start, stop #                                                 |
from labscript_utils import import_or_reload #                                      |
import_or_reload('labscriptlib.Sr.SUB_ROUTINES') #                                  |
from labscriptlib.Sr.SUB_ROUTINES import * #                                        |
#\______________________________ GENERAL LIBRARIES ________________________________/#

shield=False
shieldMulti=True

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

    t=BlueMot_load(t, GLOBALS['loadTime_BlueMOT'])

    MOT_Blue2D_AOM_TTL(t-GLOBALS['TwoD_DELAY']+dt, False)
    MOT_Blue3D_AOM_TTL(t, False)
    t+=dt
    MOT_Blue3D_Shutter_TTL(t-1*msec, True)

    t+=dt
    COILSmain_Voltage(t, 0)
    t+=dt
    COILSmain_Current(t,0)
    t+=1*usec
    COILSmain_SwitchON_TTL(t, False)
    t+=dt


    t+=dt

    ##### MULTI RED MOT #################

    MOT_Red3D_AOM_TTL(t, False)        # Luca moved this part here to turn on the comb even during the switching off
    t+=dt
    MOT_Red3D_singleFrq_TTL(t, False) 
    t+=dt
    MOT_Red3D_multiFrq_TTL(t, True)

    t+=300*usec
    COILSmain_SwitchON_TTL(t, True)

    t+=dt
    COILSmain_Voltage(t, 0.4)
    t+=dt
    COILSmain_Current(t, GLOBALS['coils_current_ctrl_red'])          # Turn on the COILSmain at 10 A, roughly 5 G/cm

    t+=GLOBALS['MOT_RED_duration']
    t+=dt
    MOT_Red3D_multiFrq_TTL(t, False)

    ##### SINGLE RED MOT #################
    
    # t+=dt
    # if sel_table_red:
    #     NEW_TABLE_LINE('RedMOT', t, GLOBALS['Red_MOT_Frq']/1e6, GLOBALS['Red_MOT_Pow'])
    # else:
    #     MOT_Red3D_AOM_TTL(t, True)     
    # t+=3*dt
    # MOT_Red3D_singleFrq_TTL(t, True)     

    # t+=GLOBALS['MOT_RED_duration']/4
  
    # MOT_Red3D_singleFrq_TTL(t, False)

    ##### END of RED #################

    COILSmain_Current(t, 0)
    t+=1*usec
    COILSmain_SwitchON_TTL(t, False)
    t+=dt

    MOT_Red3D_Switch_TTL(t, False) 

    t+=0.3*ms #for coils to switch off

    ##### ALL OFF #################
          
    

    t+=GLOBALS['TOF']# wait for time of flight
    t=take_absorbImaging(t, GLOBALS['AbsImgPulse_duration'])


    COILScomp_SwitchON_TTL(t, False)
    setoff_CompCoils(t)
    t+=10*us


stop(t)