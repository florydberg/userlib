from labscript import start, stop
from generate_samples import generate_digital_samples, generate_analog_samples, test_word
from labscript_utils import import_or_reload
import_or_reload('labscriptlib.example_apparatus.connection_table')

from labscriptlib.example_apparatus.connection_table import primary, secondary


t = board0.start_time
dt =1*board0.time_step #mu seconds
Ttot=100*dt
start()

while t < Ttot:
    digimon15.go_high(t)
    digimon1.go_high(t)

    t += dt
    digimon15.go_low(t)
    digimon1.go_low(t)

    t += dt

if False:
    # generate triangular ramps on given analog channel
        samples = int(2.5e5)
        t_start = t
        t = generate_analog_samples(AnalogOut_device=Freezer,  start_time=t, time_step=100*dt, end_time=None, num_samples=samples, Umin=-10, Umax=+10, dU=1)
        # t += dt
        # t = generate_analog_samples(AnalogOut_device=Cell, start_time=t, time_step=dt, end_time=None, num_samples=int(samples/2), Umin=-1, Umax=+1, dU=1)
        if secondary:
            t = generate_analog_samples(AnalogOut_device=Goku, start_time=t_start, time_step=dt, end_time=None, num_samples=samples, Umin=-1, Umax=+1, dU=1)
t += dt

stop(t)
