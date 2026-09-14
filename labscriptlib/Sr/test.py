from labscript import start, stop
from labscript_utils import import_or_reload
import_or_reload('labscriptlib.Sr.SUB_ROUTINES')
from labscriptlib.Sr.SUB_ROUTINES import GLOBALS
from labscriptlib.Sr.SUB_ROUTINES import *

#\______________________________ PARAMETERS ____________________________________/#

f_start = 80      # MHz
f_stop  = 120     # MHz
N_points = 41     # number of frequency points

ramp_time = 5e-3      # time to ramp between frequencies (s)
hold_time = 10e-3     # time to measure at each frequency (s)

amplitude = 100       # % (or your normalized scale)

# Generate frequency list
freqs = linspace(f_start, f_stop, N_points)

#\______________________________ SEQUENCE ______________________________________/#

start()

t = 0

# --- INITIAL CONDITION ---
AWG.dds_static(
    core=0,
    frequency=freqs[0],
    amplitude=amplitude
)

AWG.dds_setup(1)
AWG.trigger_dds()

t += hold_time


# --- SCAN LOOP ---
for i in range(len(freqs) - 1):

    f_i = freqs[i]
    f_f = freqs[i+1]

    slope = (f_f - f_i) / ramp_time  # MHz/s

    # --- RAMP ---
    AWG.dds_slope(
        core=0,
        frequency_per_sec=slope,
        amplitude=amplitude
    )

    AWG.dds_setup(1)
    AWG.trigger_dds()

    t += ramp_time

    # --- FREEZE (critical!) ---
    AWG.dds_slope(
        core=0,
        frequency_per_sec=0,
        amplitude=amplitude
    )

    AWG.dds_setup(1)
    AWG.trigger_dds()

    # --- MEASUREMENT WINDOW ---
    # Put here your camera / PD / ADC trigger
    # Example:
    # camera.expose(t, 'AOD_image', exposure_time=hold_time)

    t += hold_time


# --- OPTIONAL: RETURN TO START ---
# (useful for repeatability)
AWG.dds_slope(
    core=0,
    frequency_per_sec=(freqs[0] - freqs[-1]) / ramp_time,
    amplitude=amplitude
)

AWG.dds_setup(1)
AWG.trigger_dds()

t += ramp_time

AWG.dds_slope(
    core=0,
    frequency_per_sec=0,
    amplitude=amplitude
)

AWG.dds_setup(1)
AWG.trigger_dds()

t += hold_time


stop(t)