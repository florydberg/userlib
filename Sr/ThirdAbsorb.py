from labscript import start, stop #                                                 |
from labscript_utils import import_or_reload #                                      |
import_or_reload('labscriptlib.Sr.SUB_ROUTINES') #                                  |
from labscriptlib.Sr.SUB_ROUTINES import * #                                        |
#________________________ GENERIC LIBRARIES ________________________________________#


start()
t+=dt
ImagingBeam.DDS.setfreq(t, G_Imaging_Frq)

dueD_MOT.DDS.setfreq(t, G_dueD_MOT_Frq)

COILS_current1.constant(t, 2)

t+=5*msec

for i in range(0,GLOBALS['n_loop']):

    t=BlueMot(t, GLOBALS['loadTime_BlueMOT'], GLOBALS['MOT_duration'])

    t+=GLOBALS['TOF'] # wait for time of fligh

    t=take_absorbImaging(t, GLOBALS['AbsImgPulse_duration'])
    t+=5*sec
    
COILS_current1.constant(t, 0)
stop(t+1*sec) #to cool coils down
