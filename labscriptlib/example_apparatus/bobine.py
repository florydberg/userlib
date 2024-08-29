from labscript import start, stop
from generate_samples import generate_digital_samples, generate_analog_samples, test_word
from labscript_utils import import_or_reload
import_or_reload('labscriptlib.example_apparatus.connection_table')

from labscriptlib.example_apparatus.connection_table import *


t = board0.start_time
dt =1000000*board0.time_step #mu seconds
Ttot=100*dt
start()

    
if True:
    # generate triangular ramps on given analog channel
    samples = int(2.5e3)
    t_start = t
    t = generate_analog_samples(AnalogOut_device=BOBINE, start_time=t, time_step=1*dt, end_time=None, num_samples=samples, Umin=0, Umax=5, dU=1)
    # t = generate_analog_samples(AnalogOut_device=Cell, start_time=t_start, time_step=1*dt, end_time=None, num_samples=samples, Umin=0, Umax=5, dU=0.01)
t += dt

digimon1.go_low(t)
digimon2.go_low(t)
digimon3.go_high(t)

t += dt

stop(t)
