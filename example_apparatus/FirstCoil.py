from labscript import start, stop
from generate_samples import generate_digital_samples, generate_analog_samples, test_word
from labscript_utils import import_or_reload
import_or_reload('labscriptlib.example_apparatus.connection_table')

from labscriptlib.example_apparatus.connection_table import *
from user_devices.mogdevice import MOGDevice

t = board0.start_time
dt =30000*board0.time_step #1mu second
Ttot=100*dt
start()

if True:
    # generate triangular ramps on given analog channel
    samples = int(2.5e3)
    t_start = t
    COILS.constant(t, 1.1)
    t=+dt
    COILS.constant(t, 0.0)

stop(t+dt)
