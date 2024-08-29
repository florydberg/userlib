#___________________________________________________________________________________#
from labscript import start, stop #                                                 |
from labscript_utils import import_or_reload #                                      |
import_or_reload('labscriptlib.Sr.SUB_ROUTINES') #                                  |
from labscriptlib.Sr.SUB_ROUTINES import * #                                        |
#\______________________________ GENERAL LIBRARIES ________________________________/#

start()
i=0

for i in range(0,10):
    
    t+=100*msec
    Andor_Camera_trigger.go_high(t)
    delay=Andor_Camera.expose(t+dt, str(i), frametype='tiff') 
    BlueImaging_AOM_TTL(t+10*usec, True)
    t+=+5*usec
    
    t+=10*msec   
    Andor_Camera_trigger.go_low(t)
    t+=delay
    BlueImaging_AOM_TTL(t, False)
    t+=300*msec

stop(t)