from labscript import start, stop
from generate_samples import generate_digital_samples, generate_analog_samples, test_word
from labscript_utils import import_or_reload
import_or_reload('labscriptlib.example_apparatus.connection_table')

from labscriptlib.example_apparatus.connection_table import *


t = board0.start_time
dt =1000000*board0.time_step #1mu second
Ttot=100*dt
start()

# primary.set_sync_params(wait=11)
# secondary.set_sync_params(wait=0,phase=(int(3/10*560))<<10)

while t < Ttot:

    if True:
        pokemon1.go_high(t)
        digimon1.go_high(t)
        digimon2.go_low(t)
        digimon3.go_low(t)
        digimon4.go_low(t)

        # duration = 4*(2**16)*1e-6
        # Freezer.ramp(t=t, initial= 0.0, final= 9.0, duration=duration/4, samplerate=1e6)

        t += 1*dt

        pokemon1.go_low(t)
        digimon1.go_low(t)
        digimon2.go_high(t)
        digimon3.go_low(t)
        digimon4.go_low(t)

        t += 1*dt

        digimon1.go_low(t)
        digimon2.go_low(t)
        digimon3.go_high(t)
        digimon4.go_low(t)

        t += 1*dt
        
        digimon1.go_low(t)
        digimon2.go_low(t)
        digimon3.go_low(t)
        digimon4.go_high(t)

        t += 1*dt


    
if False:
    # generate triangular ramps on given analog channel
    samples = int(2.5e3)
    t_start = t
    t = generate_analog_samples(AnalogOut_device=Cell, start_time=t_start, time_step=1*dt, end_time=None, num_samples=samples, Umin=-10, Umax=10, dU=0.01)
    if secondary:
            t = generate_analog_samples(AnalogOut_device=Goku, start_time=t_start, time_step=dt, end_time=None, num_samples=samples, Umin=-1, Umax=+1, dU=1)


if False:
    if True: # fastest ramp possible with 1 sample per us
        duration = 4*(2**16)*1e-6
    else: # 5s in total
        duration = 5.0
    for i in range(8):
        # this creates an analog ramp from -10V to +10V and back with maximum sample rate of 1MHz.
        # for 16bits the voltage resolution is 20V/2^16 = 0.3mV.
        # if you increase the duration the true SampleRate will go down. this is not a problem with labscript or ramp,
        # but is a concequence that FPGA_device generates output only when the channel is changing.
        # for 16 bits voltage resolution and more than 2^16 samples not every sample can change the voltage.
        t += dt
        #t += Freezer.ramp(t=t, initial=-10.0, final= 10.0, duration=(2**16)*1e-6, samplerate=1e6)
        #t += Freezer.ramp(t=t, initial= 10.0, final=-10.0, duration=(2**16)*1e-6, samplerate=1e6)
        t_start = t
        t += Freezer.ramp(t=t, initial= 0.0, final= 9.0, duration=duration/4, samplerate=1e6)
        t += Freezer.ramp(t=t, initial= 9.3, final=-9.0, duration=duration/2, samplerate=1e6)
        t += Freezer.ramp(t=t, initial=-9.3, final= 0.0, duration=duration/4, samplerate=1e6)
        if secondary is not None: # parallel ramp on secondary board
            t = t_start
            t += Goku.ramp(t=t, initial=0.0, final=9.0, duration=duration/4, samplerate=1e6)
            t += Goku.ramp(t=t, initial=9.3, final=-9.0, duration=duration/2, samplerate=1e6)
            t += Goku.ramp(t=t, initial=-9.3, final=0.0, duration=duration/4, samplerate=1e6)

t += dt


digimon1.go_low(t)
digimon2.go_low(t)
digimon3.go_high(t)
pokemon1.go_high(t)

t += dt

stop(t)
