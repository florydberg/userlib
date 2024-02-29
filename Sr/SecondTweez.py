from labscript import start, stop
from labscript_utils import import_or_reload
import_or_reload('labscriptlib.Sr.SUB_ROUTINES')
from labscriptlib.Sr.SUB_ROUTINES import *

#globals
ToF=TOF*usec
Tweez_duration=Tweezer_duration*msec
beam_duration=ImgBeam_duration*usec
fluo_duration=Fluorescence_duration*usec
MOT_time=MOT_duration*usec

start()

for i in range(0,n_loop):   

    t+=BlueMot(t, loadingMOT_time, twoD_delay, MOT_time)

    t+=ToF # wait for time of flight

    t+=take_absorbImaging(t, beam_duration)

    # ------------------------------------------------------------#

    t+=BlueMot(t, loadingMOT_time, twoD_delay, MOT_time)

    t+=do_Tweezer(t-Tweez_duration/2, Tweez_duration/2)

    t+=take_fluoImagig(t)

stop(t+5*sec)