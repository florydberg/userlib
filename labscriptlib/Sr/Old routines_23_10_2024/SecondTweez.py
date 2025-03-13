from labscript import start, stop
from labscript_utils import import_or_reload
import_or_reload('labscriptlib.Sr.SUB_ROUTINES')
from labscriptlib.Sr.SUB_ROUTINES import *

# check_global_remote()

#globals
G_TOF=TOF*usec
G_Tweezer_duration=Tweezer_duration*msec
G_AbsImgPulse_duration=AbsImgPulse_duration*usec
G_FluoImgPulse_duration=FluoImgPulse_duration*usec
G_MOT_time=MOT_duration*usec

start()

for i in range(0,n_loop):   

    t+=BlueMot(t, G_loadTime_BlueMOT, G_MOT_time)

    t+=do_Tweezer(t-G_Tweezer_duration/2, G_Tweezer_duration/2)

    t+=take_fluoImagig(t)

stop(t+1*sec)