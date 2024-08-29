#___________________________________________________________________________________#
from labscript import start, stop #                                                 |
from labscript_utils import import_or_reload #                                      |
import_or_reload('labscriptlib.Sr.SUB_ROUTINES') #                                  |
from labscriptlib.Sr.SUB_ROUTINES import * #                                        |
#\______________________________ GENERAL LIBRARIES ________________________________/#

start()
t+=100*dt

#TABLE MODE ON
TABLE_MODE_ON('Free', t)

t+=100*usec

# NEW VALUE
NEW_TABLE_LINE('Free', t, 10, 10)

t+=100*usec

# NEW VALUE
NEW_TABLE_LINE('Free', t, 20, 29)

t+=100*usec

# TABLE OFF
TABLE_MODE_OFF('Free', t)


t+=100*usec

stop(t+1*msec)