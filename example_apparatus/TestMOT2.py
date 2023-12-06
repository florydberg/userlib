from labscript import *
from labscript import start, stop
from labscript_utils import import_or_reload
import_or_reload('labscriptlib.example_apparatus.connection_table')
from generate_samples import generate_digital_samples, generate_analog_samples, test_word
from labscriptlib.example_apparatus.connection_table import *

t = board0.start_time
dt =10*board0.time_step #mu seconds
Ttot=1000*dt
start()

# primary.set_sync_params(wait=600000)
# secondary.set_sync_params(wait=0,phase=(int(3/10*560))<<10)

if True:
    # generate triangular ramps on given analog channel
    samples = int(3e3)
    t_start = t
    t = generate_analog_samples(AnalogOut_device=Freezer, start_time=t, 
                                time_step=1*dt, end_time=None, num_samples=samples, Umin=0, Umax=+10, dU=0.1)
    t += dt
    if secondary:
        t = t_start
        t = generate_analog_samples(AnalogOut_device=Goku, start_time=t, 
                                    time_step=dt, end_time=None, num_samples=samples, Umin=0, Umax=+10, dU=0.1)
    t += dt

if False:
    if True: # fastest ramp possible with 1 sample per us
        duration = 4*(2**16)*1e-6
    else: # 5s in total
        duration = 5.0
    for i in range(8):
        t += dt
        #t += coil_x.ramp(t=t, initial=-10.0, final= 10.0, duration=(2**16)*1e-6, samplerate=1e6)
        #t += coil_x.ramp(t=t, initial= 10.0, final=-10.0, duration=(2**16)*1e-6, samplerate=1e6)
        t_start = t
        t += Freezer.ramp(t=t_start, initial= 0.0, final= 9.0, duration=duration/4, samplerate=1e6)
        t += Freezer.ramp(t=t, initial= 9.3, final=-9.0, duration=duration/2, samplerate=1e6)
        t += Freezer.ramp(t=t, initial=-9.3, final= 0.0, duration=duration/4, samplerate=1e6)
        t = t_start
        t += Goku.ramp(t=t, initial= 0.0, final= 9.0, duration=duration/4, samplerate=1e6)
        t += Goku.ramp(t=t, initial= 9.3, final=-9.0, duration=duration/2, samplerate=1e6)
        t += Goku.ramp(t=t, initial=-9.3, final= 0.0, duration=duration/4, samplerate=1e6)

f0=0
f1=123 #MHz
duration = 5.0
QRF_MOT.program_static(3, 'freq', f1)

stop(t)