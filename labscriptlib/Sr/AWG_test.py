#___________________________________________________________________________________#
from labscript import start, stop #                                                 |
from labscript_utils import import_or_reload #                                      |
import_or_reload('labscriptlib.Sr.SUB_ROUTINES') #                                  |
from labscriptlib.Sr.SUB_ROUTINES import * #                                        |
#\______________________________ GENERAL LIBRARIES ________________________________/#

test_frequencies=[1e7,1.1e7,1.2e7]
test_amplitudes= [1/2,1,1/2]
start()
t+=10*msec
set_MOGLABS_ready(t)
t+=10*msec

for i in range(GLOBALS['n_loop']):
    t+dt
    Vertical.generate_multiple_tones(t,sample_duration=2e-1, frequencies=test_frequencies, amplitudes=test_amplitudes, label='vertical'+str(i)) # duration in s, frq in Hz
    Horizontal.generate_multiple_tones(t,sample_duration=2e-1,frequencies=test_frequencies, amplitudes=test_amplitudes, label='horizontal'+str(i))
    awg_trigger.go_high(t)
    awg_trigger.go_low(t+1*msec)
    t+=10*msec

stop(t+GLOBALS['stop_buffering_time'])