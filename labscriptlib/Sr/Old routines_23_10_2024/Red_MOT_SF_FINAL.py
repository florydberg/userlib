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

    t=RedBroad_Mot_Test(t, GLOBALS['MOT_RED_duration'], GLOBALS['loadTime_BlueMOT'], shield=False, shieldMulti=True)        #Same function as always but the small coils are not turned off
    # t=RedBroad_Mot_Final(t, GLOBALS['MOT_RED_duration'], GLOBALS['loadTime_BlueMOT'], shield=False, shieldMulti=True)
    t+=dt
    
    # MOT_Red3D_Switch_TTL(t, True) 
    # t+=dt
    # MOT_Red3D_AOM_TTL(t, True)        #Luca moved this part here to turn on the comb even during the switching off
    # t+=dt
    # MOT_Red3D_singleFrq_TTL(t, True)  
    # t+=dt

    t+=GLOBALS['TOF'] # wait for time of flight

    
    # Sisyphus_AOM_TTL(t-(GLOBALS['TOF']-300*us), True)         #For red spectroscopy


    # MOT_Red3D_Switch_TTL(t, False) 
    # t+=dt
    # MOT_Red3D_AOM_TTL(t, False)        #Luca moved this part here to turn on the comb even during the switching off
    # t+=dt
    # MOT_Red3D_singleFrq_TTL(t, False)  
    # t+=dt

    t=take_absorbImaging(t, GLOBALS['AbsImgPulse_duration'])

    # t=take_fluoImaging_Andor(t+dt,'Fluo')

    COILScomp_SwitchON_TTL(t, False)

    setoff_CompCoils(t)
    t+=10*us

stop(t)