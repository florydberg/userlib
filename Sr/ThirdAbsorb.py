from labscript import start, stop
from labscript_utils import import_or_reload
import_or_reload('labscriptlib.Sr.SUB_ROUTINES')
from labscriptlib.Sr.SUB_ROUTINES import *
############################################################################################
CALIBR=0     #1 yes, 0 no                                                                 ##
if CALIBR: G_Imaging_Frq=GLOBALS['CAL_Imaging_Frq']/1e6                                   ##
else:G_Imaging_Frq=GLOBALS['Imaging_Frq']/1e6                                             ##
MogLabs_newvalue('blue', 4, 'FREQ', G_Imaging_Frq)                                        ##
############################################################################################

start()

for i in range(0,GLOBALS['n_loop']): 
    
    t+=BlueMot(t, GLOBALS['loadTime_BlueMOT'], GLOBALS['MOT_duration'])

    t+=GLOBALS['TOF'] # wait for time of flight

    t+=take_absorbImaging(t, GLOBALS['AbsImgPulse_duration'])

stop(t+1*sec)
