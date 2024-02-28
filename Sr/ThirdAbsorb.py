from labscript import start, stop
from labscript_utils import import_or_reload
import_or_reload('labscriptlib.Sr.SUB_ROUTINES')
from labscriptlib.Sr.SUB_ROUTINES import *

ToF=TOF*usec

start()

for i in range(0,n_loop):    

    t+=BlueMot(t, loadingMOT_time, twoD_delay, MOT_duration*usec)

    t+=ToF # wait for time of flight

    t+=take_absorbImaging(t)

stop(t)