#___________________________________________________________________________________#
from labscript import start, stop #                                                 |
from labscript_utils import import_or_reload #                                      |
import_or_reload('labscriptlib.Sr.SUB_ROUTINES') #                                  |
from labscriptlib.Sr.SUB_ROUTINES import * #                                        |
#\______________________________ GENERAL LIBRARIES ________________________________/#

start()
t+=dt
set_MOGLABS_ready(dt)

IGBT_close.go_high(t)
t+=5*msec
BigCoilsI.constant(t, 2)
t+=200*msec

#Io test
# BigCoilsI.constant(t, 0)
# t+=50*usec

#IIo test
# BigCoilsI.constant(t, 0.15)
# t+=50*msec
# BigCoilsI.constant(t, 0.0)

#IIIo test
BigCoilsI.constant(t, 0.15)
t+=500*usec
IGBT_close.go_low(t)
t+=300*usec
IGBT_close.go_high(t)
t+=50*msec
BigCoilsI.constant(t, 0.0)

stop(t+dt)