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

for i in range(0,GLOBALS['n_loop']):

    COILScomp_SwitchON_TTL(t, True)
    set_CompCoils(t+5*us)    

    # t=RedBroad_Mot(t, GLOBALS['MOT_RED_duration'], GLOBALS['loadTime_BlueMOT'], shield=False, shieldMulti=True)        #Same function as always but the small coils are not turned off
    t=RedBroad_Mot_Final(t, GLOBALS['MOT_RED_duration'], GLOBALS['loadTime_BlueMOT'], shield=False, shieldMulti=True)
    t+=dt
    # IGBT_close.go_high(t)

    # t+=1*msec
    # BigCoilsI.constant(t, GLOBALS['coils_current_cntrl'])       #Turns on the big coils again

    # t+=dt
    # treD_MOT_gate.go_high(t) # 3D MOT                           #Turns on the blue 3D MOT beam again

    # t+=GLOBALS['T_BlueMolass']                                  #Waits for a variable time where the atoms are held in the blue mot

    # t+=dt
    # treD_MOT_gate.go_low(t) # 3D                                #Turns off the blue 3d mot beams and the coils
    # t+=dt
    # BigCoilsI.constant(t, 0)

    # t+=1*usec

    # IGBT_close.go_low(t)
    # t+=dt
    # Shutter_Blue.go_high(t)                                     #Restores the shutter position to closed
    # t+=dt
    # treD_MOT_gate.go_high(t+3*msec) # 3D MOT +3*msec

    # Red_commonSwitch.go_low(t)       #Luca commented this part to use the4 function in RED_MOT_Salvi
    # Red_multiFrq.go_low(t)  

    t+=GLOBALS['TOF'] # wait for time of flight
    
    t=take_absorbImaging(t, GLOBALS['AbsImgPulse_duration'])

    COILScomp_SwitchON_TTL(t, False)

    setoff_CompCoils(t)
    t+=10*us

stop(t)