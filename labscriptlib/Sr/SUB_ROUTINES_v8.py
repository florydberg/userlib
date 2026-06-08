########## SUB ROUTINES #######################
# by Andrea for Sr FloRydberg Group           #
# register of actions for Labscript Ruotines  #
# last edited 03/07/2024                      # 
###############################################
from user_devices.MOGlabsQRF.mogdevice import MOGDevice
import runmanager.remote
import h5py
import math 
import numpy as np
import csv
from scipy.signal import hilbert
from PIL import Image
import os
from labscript_utils import import_or_reload
import_or_reload('labscriptlib.Test_AWG_Spectrum.connection_table')
from labscriptlib.Test_AWG_Spectrum.connection_table import *
from labscript_utils.shot_utils import get_shot_globals

if True: # Time Constants
    t=0
    dt=main_board.time_step # 1 us
    usec=dt
    us=usec
    msec=1000*dt
    ms=msec
    sec=1000000*dt
    s=sec
    min=60*sec

def import_GLOBALS(settings_path): #init of globals and times
    units={}
    for globals_group  in runmanager.get_grouplist(settings_path):
        for global_name in runmanager.get_globalslist(settings_path, globals_group):
            with h5py.File(settings_path,'r') as shot_h5py: global_units =  shot_h5py["globals"][globals_group]["units"].attrs[global_name]
            if global_units=='us': #base unit for time
                g_unit=usec
            elif global_units=='ms':
                g_unit=msec
            elif global_units=='s':
                g_unit=sec
            elif global_units=='Hz':#base unit for frequency
                g_unit=1
            elif global_units=='kHz':
                g_unit=1e3
            elif global_units=='MHz':
                g_unit=1e6
            else:
                g_unit=1
            units[str(global_name)]=g_unit
    GLOBALS={}
    for i in runmanager.remote.get_globals():
        print(i)
        GLOBALS[str(i)]=eval(i)*units[str(i)]


    return GLOBALS

shot_settings_path='F:\\Experiments\\Sr\\SrParameters.h5'
GLOBALS=import_GLOBALS(shot_settings_path) # import GLOBALS from the shot file

if True: # === AWG Tweezer Embedding ===
    # --- Imports ---
    import numpy as np
    import csv
    from scipy.signal import hilbert

    # --- Define Points on a 10 µm Square Grid ---
    if not GLOBALS['reordering_mode']:
        zooming=GLOBALS['zooming']
        points_dict = {}
        edges_list = []
        grid_size = GLOBALS['grid_size']
        ranging = 200 * zooming  # µm
        coords = np.linspace(-ranging, +ranging, grid_size)
        step_lenght = 2 * ranging /(grid_size - 1)

        index = 0
        for y in coords:
            for x in coords:
                points_dict[f'P{index}'] = (x, y)
                # print(f"({x},{y})")
                index += 1
    else:
        zooming=GLOBALS['zooming']
        points_dict = {}
        edges_list = []
        ranging = 200 * zooming  # µm
        geometry_path = str(GLOBALS['geometry_path']+".h5")
        with h5py.File(geometry_path, 'r') as f:
            coords = f['points'][:]
            index = 0
            for x, y in coords:
                points_dict[f'P{index}'] = (x, y)
                index += 1
            edges_list = f['edges'][:]
        step_lenght = 2 * ranging /(len(points_dict)**(0.5)- 1)

    # print(f"Points dictionary: {points_dict}"
    #       f" with {step_lenght} step lenght")



    # --- Constants ---
    CALIBRATION_X = GLOBALS['CALIBRATION_X']  # Hz/µm
    CALIBRATION_Y = GLOBALS['CALIBRATION_Y']
    FREQ_CENTER_X = GLOBALS['FREQ_CENTER_X']  # Hz
    FREQ_CENTER_Y = GLOBALS['FREQ_CENTER_Y']
    CALIBRATION_V = GLOBALS['CALIBRATION_V']  # 1 mK → 1 V
    global_amp_max_corr = (GLOBALS['global_int_max']/100)**0.5
    Tweezer_intensity_corr = (GLOBALS['Tweezer_intensity']/100)**0.5

    sample_rate = Awg_sampleRate  # Hz

    # --- Utility Functions ---

    class TweezerLUT:
        def __init__(self, image_path, normalize=True):
            self.image_path = image_path
            self.calibration = {
                'horizontal': (CALIBRATION_X, FREQ_CENTER_X),
                'vertical': (CALIBRATION_Y, FREQ_CENTER_Y)
            }
            self.normalize = normalize
            self._lut_image = None  # Lazy load
            self.pixel_size_um = GLOBALS['pixel_dimension']
            self.LUT_ratio=0
            self.n_pixels=GLOBALS['n_pixels_LUT']

        def _load_lut_image(self):
            if self._lut_image is None:
                if not os.path.exists(self.image_path):
                    raise FileNotFoundError(f"LUT image not found: {self.image_path}")

                img = Image.open(self.image_path).convert('L')  # Grayscale
                lut = np.array(img, dtype=np.float32)
                height, width = lut.shape
                sigma=self.n_pixels//2
                lut = lut[height // 2 - sigma : height // 2 + sigma ,  width // 2 - sigma  : width // 2 + sigma ]

                if self.normalize:
                    # True amplitude map: normalize to [0, 1]
                    lut /= lut.max()

                    # Compute correction map: correction = max_amp / lut
                    min_val = lut[lut > 0].min()  # avoid division by zero
                    max_val = lut.max()

                    correction = max_val / (lut + 1e-6)  # add epsilon to avoid /0
                    correction *= min_val / max_val     # scale so that min → 1.0, max → min/max

                    self.LUT_ratio = min_val / max_val 

                    lut = correction

                    self._lut_image = lut

            return self._lut_image
    
        def GaussCorrection(self, move_type, freq_bins):
            corr_a = GLOBALS['GAUSS_CALIBRATION_peak']/100
            corr_b = 1 - corr_a
            if move_type == 'horizontal':
                sigma = GLOBALS['corr_sigma_x']
            elif move_type == 'vertical':
                sigma = GLOBALS['corr_sigma_y']
            calibration, center_freq = self.calibration[move_type]
            arg=(freq_bins - center_freq) / calibration / sigma
            gauss = np.exp(-0.5 * ( arg ) ** 2)
            return corr_a + corr_b * (1 - gauss)

        def get_amp_correction(self, freqs, axis='horizontal'):
            """
            freqs: array-like of frequencies [Hz]
            axis: 'horizontal' or 'vertical'
            """
            freqs = np.asarray(freqs)
            if axis not in self.calibration:
                raise ValueError("Axis must be 'horizontal' or 'vertical'")

            # Convert frequencies to positions (μm)
            a, b = self.calibration[axis]
            pos_um = (freqs - b) / a

            # Load LUT image and take central profile along the axis
            lut = self._load_lut_image()
            # print(np.max(lut))
            height, width = lut.shape
            profile = lut[height // 2, :] if axis == 'horizontal' else lut[:, width // 2]

            # Position → pixel index conversion
            n_pixels = self.n_pixels
            pixel_size = self.pixel_size_um
            total_range_um = n_pixels * pixel_size
            half_range_um = total_range_um / 2.0

            indices = (pos_um + half_range_um) / total_range_um * (n_pixels - 1)
            indices = np.clip(indices, 0, n_pixels - 1)

            # Interpolate LUT value
            # print(f"{n_pixels}...{len(profile)}")
            lut_vals = np.interp(indices, np.arange(n_pixels), profile)

            # print(f"correction values {np.max(lut_vals)}, {np.min(lut_vals)} for {axis}")

            # Final correction: linearly scaled
            correction = lut_vals**0.5

            return correction
    
    LUT_Tweezer = TweezerLUT(GLOBALS['LUT_path'])

    def get_instantaneous_frequency(signal, dt):
        analytic_signal = hilbert(signal)
        phase = np.unwrap(np.angle(analytic_signal))
        return np.diff(phase) / (2 * np.pi * dt)

    def Temperature_to_RF(A):
        return CALIBRATION_V * A

    def Ver_position_to_frequency(y):
        return FREQ_CENTER_Y + CALIBRATION_Y * y

    def Hor_position_to_frequency(x):
        return FREQ_CENTER_X + CALIBRATION_X * x

    def detect_move_type(p_start, p_end):
        x0, y0 = p_start
        x1, y1 = p_end
        if x0 == x1:
            return 'vertical', 1 if y1 > y0 else -1, y0
        elif y0 == y1:
            return 'horizontal', 1 if x1 > x0 else -1, x0
        else:
            direction = [1 if x1 > x0 else -1, 1 if y1 > y0 else -1]
            return 'oblique', direction, (x0, y0)

    def get_pos_to_freq_func(move_type):
        if move_type == 'horizontal':
            return Hor_position_to_frequency
        elif move_type == 'vertical':
            return Ver_position_to_frequency
        elif move_type == 'oblique':
            return lambda xy: np.sqrt(
                Hor_position_to_frequency(xy[0])**2 +
                Ver_position_to_frequency(xy[1])**2
            )

    def read_tweezer_csv(csv_path):
        steps = []
        if csv_path is not None:
            with open(csv_path, newline='') as csvfile: 
                reader = csv.DictReader(csvfile)
                for row in reader:
                    steps.append({
                        't': float(row['t']),
                        'x': float(row['x']) / 8.45 * step_lenght, #*ranging/grid_size*zooming/10
                        'A': float(row['A']) * -10000 / 1.7
                    })
        else:
            for ii in range(0,2):
                # print("csv_not available: default values")
                steps.append({
                    't': float(10*ii),
                    'x': float(ranging*2*ii),
                    'A': float(1)
                })
            # print(steps)

        return steps

    def generate_samples(schedule, dtt, duration, cutting, pos_to_freq_func, move_type, direction, starting_point, linear_ramp , oblique_mode = False,):
        samples = []
        last_time = schedule[0]['t'] * 1e-6
        sequence_offset = schedule[0]['x']
        last_amp = Temperature_to_RF(schedule[0]['A'])
        last_freq = pos_to_freq_func(starting_point)
        
        segment_lenght = max(step['x'] for step in schedule) + max((-step['x']) for step in schedule)
        AWG_max=32767
        max_amp = max(abs(step['A']) for step in schedule)
        norm_factor = AWG_max / max_amp if max_amp else AWG_max

        phase_accum = 0
        fs = len(dtt) / duration
        freq_bins = np.fft.rfftfreq(len(dtt), d=1/fs)
        inv_gauss = LUT_Tweezer.GaussCorrection(move_type, freq_bins)

        ii=0

        # print(len(schedule))
        for step in schedule[0:]:
            time = step['t'] * 1e-6
            
            if linear_ramp: # linear ramp
                # amp = max_amp
                amp = Temperature_to_RF(step['A'])
                pos = starting_point + direction * (segment_lenght/(len(schedule)-1)*(ii))
                freq = pos_to_freq_func(pos)
            
                # print(segment_lenght)
                # print(f"{segment_lenght/len(schedule)*ii } um step")
                # print(f"{pos} um coordinate")
                # print(f"{ii+1} / {len(schedule)}")
                # print(f"{freq} Hz ")
                ii+=1
            else:
                amp = Temperature_to_RF(step['A'])
                # amp = max_amp
                pos = starting_point + direction * (step['x'] - sequence_offset)
                # print(f"{step['x']} um data value")
                # print(f"{pos} um target coordinate")

                # print(f"{time},")
                freq = pos_to_freq_func(pos)

            segment_dtt = dtt[(dtt >= last_time) & (dtt < time)]

            if len(segment_dtt) > 1:

                dt = segment_dtt[1] - segment_dtt[0]
                freq_interp = np.interp(segment_dtt, [last_time, time], [last_freq, freq])

                # Frequency-dependent amplitude correction
                freq_indices = np.searchsorted(freq_bins, freq_interp, side='left')
                freq_indices = np.clip(freq_indices, 0, len(inv_gauss) - 1)

                amp_interp = np.interp(segment_dtt, [last_time, time], [last_amp, amp])
                amp_interp *= norm_factor

                Gauss_corr = inv_gauss[freq_indices] if GLOBALS['Gauss_corr'] else 1
                LUT_corr = LUT_Tweezer.get_amp_correction(freq_interp, axis=move_type) if GLOBALS['LUT_corr'] else 1

                # print(f"Target amp value = {amp}")

                # print(f"Gauss correction = {np.max(Gauss_corr)}")
                # print(f"LUT correction = [{np.max(LUT_corr)}, {np.min(LUT_corr)}]")
                # print(f"Tweezer power correction = {Tweezer_intensity_corr}")


                amp_interp *= Gauss_corr * LUT_corr 
                Twintensity_corr = Tweezer_intensity_corr
                if oblique_mode:
                    # print((amp_interp / AWG_max)** 0.25 )
                    amp_interp = (amp_interp / AWG_max) ** 0.5 * AWG_max
                    Twintensity_corr **= 0.5

                # print(f"last value = {amp_interp}")

                phase = phase_accum + 2 * np.pi * np.cumsum(freq_interp) * dt
                phase_accum = phase[-1]

                segment_samples = np.int16(np.array(amp_interp * np.sin(phase) * Twintensity_corr)) 
                samples.extend(segment_samples)
                
            last_time, last_amp, last_freq = time, amp, freq

        # Tail segment
        segment_dtt = dtt[(dtt >= last_time) & (dtt < duration)]
        cut_length = 0
        if len(segment_dtt) > 1:
            dt = segment_dtt[1] - segment_dtt[0]
            if cutting:
                last_amp = 0
                cut_length = len(segment_dtt)
            amp_tail = np.full_like(segment_dtt, last_amp * norm_factor)
            freq_tail = np.full_like(segment_dtt, last_freq)
            phase = phase_accum + 2 * np.pi * np.cumsum(freq_tail) * dt
            segment_samples = np.int16(amp_tail * np.sin(phase))
            samples.extend(segment_samples)

        return samples, cut_length

    def standing_wave(frequencies, amplitudes, phases, num_samples, duration, print_crest_factor=False):
        frequencies = np.asarray(frequencies)
        amplitudes = np.asarray(amplitudes)
        phases = np.asarray(phases)
        dtt = np.linspace(0, duration, num_samples, endpoint=False)
        signal = sum(a * np.sin(2 * np.pi * f * dtt + p) for f, a, p in zip(frequencies, amplitudes, phases))
        peak = np.abs(signal).max()
        max_a = np.abs(amplitudes).max()
        if peak:
            signal *= 32767 / peak / 100 * max_a
        if print_crest_factor:
            crest = 32767 / np.sqrt(np.mean(signal ** 2))
            print(f"Crest factor: {crest:.3f}")
        return np.int16(signal)

    def standing_wave_equalized(frequencies, num_samples, duration, print_crest_factor=False):
        fs = num_samples / duration
        freq_bins = np.fft.rfftfreq(num_samples, d=1/fs)
        spectrum = np.zeros(len(freq_bins), dtype=np.complex128)
        for f in frequencies:
            idx = np.argmin(np.abs(freq_bins - f))
            spectrum[idx] = 1.0
        signal = np.fft.irfft(spectrum, n=num_samples)
        peak = np.max(np.abs(signal))
        if peak:
            signal *= 32767 / peak
        if print_crest_factor:
            crest = 32767 / np.sqrt(np.mean(signal ** 2))
            print(f"Crest factor: {crest:.2f}")
        return np.int16(signal)

    def standing_wave_inverse_gaussian(move_type, frequencies, num_samples, duration, print_crest_factor=False):
        fs = num_samples / duration
        freq_bins = np.fft.rfftfreq(num_samples, d=1/fs)
        inv_gauss = LUT_Tweezer.GaussCorrection(move_type, freq_bins)
        spectrum = np.zeros(len(freq_bins), dtype=np.complex128)
        for f in frequencies:
            idx = np.argmin(np.abs(freq_bins - f))
            Gauss_corr = inv_gauss[idx] if GLOBALS['Gauss_corr'] else 1
            LUT_corr = LUT_Tweezer.get_amp_correction(f, axis=move_type) if GLOBALS['LUT_corr'] else 1
            spectrum[idx] = Gauss_corr *LUT_corr
            # print(inv_gauss[idx])
        signal = np.fft.irfft(spectrum, n=num_samples) 
        peak = np.max(np.abs(signal))
        if peak:
            signal *= 32767 / peak * global_amp_max_corr
        if print_crest_factor:
            crest = 32767 / np.sqrt(np.mean(signal ** 2))
            print(f"Crest factor: {crest:.2f}")
        return np.int16(signal)

    def standing_wave_LUT(move_type, frequencies, num_samples, duration, print_crest_factor=False):
        fs = num_samples / duration
        freq_bins = np.fft.rfftfreq(num_samples, d=1/fs)
        inv_gauss = LUT_Tweezer.GaussCorrection(move_type, freq_bins)
        spectrum = np.zeros(len(freq_bins), dtype=np.complex128)
        for f in frequencies:
            idx = np.argmin(np.abs(freq_bins - f))
            Gauss_corr = inv_gauss[idx] if GLOBALS['Gauss_corr'] else 1
            LUT_corr = LUT_Tweezer.get_amp_correction(f, axis=move_type) if GLOBALS['LUT_corr'] else 1
            spectrum[idx] = Gauss_corr *LUT_corr
            # print(inv_gauss[idx])
        signal = np.fft.irfft(spectrum, n=num_samples) 
        peak = np.max(np.abs(signal))
        if peak:
            signal *= 32767 / peak * global_amp_max_corr
        if print_crest_factor:
            crest = 32767 / np.sqrt(np.mean(signal ** 2))
            print(f"Crest factor: {crest:.2f}")
        return np.int16(signal * Tweezer_intensity_corr) 
    
    # --- Main Control Function ---
    def movingTweezer(tt, Pi, Pf, linear_ramp=False):
        move_duration = GLOBALS['move_duration']
        cutting = GLOBALS['cutting']
        csv_path = f"T{int(move_duration)}.csv"
        schedule = read_tweezer_csv(csv_path)

        start_point = points_dict[f'P{Pi}']
        end_point = points_dict[f'P{Pf}']
        step_label = f"move_{Pi}_{Pf}"


        move_type, direction, offset = detect_move_type(start_point, end_point)
        pos_to_freq_func = get_pos_to_freq_func(move_type)

        duration = (schedule[-1]['t'] - schedule[0]['t']) * 1e-6
        num_samples = int(np.round(duration * sample_rate / 4096) * 4096) + 4096
        duration = num_samples / sample_rate
        dtt = np.linspace(0, duration, num_samples, endpoint=False)

        if move_type in ['horizontal', 'vertical']:
            samples, cut_len = generate_samples(schedule, dtt, duration, cutting,pos_to_freq_func, move_type, direction, offset, linear_ramp)
            axis = Horizontal if move_type == 'horizontal' else Vertical
            axis.pass_sample(tt, samples, step_label)

            static_axis = Vertical if move_type == 'horizontal' else Horizontal
            static_coord = end_point[1] if move_type == 'horizontal' else end_point[0]
            freq = Ver_position_to_frequency(static_coord) if move_type == 'horizontal' else Hor_position_to_frequency(static_coord)
            sample_static = standing_wave_inverse_gaussian('vertical' if move_type == 'horizontal' else 'horizontal',[freq], num_samples, duration)
            if cutting:
                sample_static[-cut_len:] = 0
            static_axis.pass_sample(tt, sample_static, step_label)

        elif move_type == 'oblique':
            short_oblique = 1
            short_oblique = 0.7071
            samples_H, _ = generate_samples(schedule, dtt, duration, cutting,Hor_position_to_frequency, 'horizontal', direction[0] * short_oblique, offset[0], linear_ramp, oblique_mode=True)
            samples_V, _ = generate_samples(schedule, dtt, duration, cutting,Ver_position_to_frequency, 'vertical', direction[1] * short_oblique, offset[1], linear_ramp, oblique_mode=True)
            Horizontal.pass_sample(tt, samples_H, step_label)
            Vertical.pass_sample(tt, samples_V, step_label)
        
        return duration * usec

    def standingTweezer(tt, Points, amplitude, duration):
        """
        Generate a composite standing wave signal for multiple tweezers,
        each defined by its point index in Points.

        Parameters:
            tt: Time or AWG context object.
            Points: list or int — indices into points_dict (e.g., 1 or [1, 5, 18, 0]).
            amplitude: scalar or list — amplitude(s) in percent (single or per-point).
            duration: duration in microseconds.
        """
        if isinstance(Points, int):
            Points = [Points]
        if isinstance(amplitude, (int, float)):
            amplitude = [amplitude] * len(Points)

        sample_duration = duration * 1e-6
        norm_num_samples = int(np.round(sample_duration * sample_rate / 4096) * 4096) + 4096
        norm_sample_duration = norm_num_samples / sample_rate

        # Get positions
        xs = []
        ys = []
        for point in Points:
            x, y = points_dict[f'P{point}']
            xs.append(x)
            ys.append(y)

        # Convert positions to frequencies
        fxs = [Hor_position_to_frequency(x) for x in xs]
        fys = [Ver_position_to_frequency(y) for y in ys]

        # Generate composite signals
        sample_Hor = standing_wave_LUT('horizontal', fxs, norm_num_samples, norm_sample_duration)
        sample_Ver = standing_wave_LUT('vertical', fys, norm_num_samples, norm_sample_duration)

        # Pass signals (single composite wave per axis)
        Horizontal.pass_sample(tt, sample_Hor, f'standing_{Points}')
        Vertical.pass_sample(tt, sample_Ver, f'standing_{Points}')

        return duration * usec

    def AllTheWay(tt, Pi, move_type):
        move_duration = 1e-5
        cutting = GLOBALS['cutting']
        schedule = read_tweezer_csv(None)

        start_point = points_dict[f'P{Pi}']
        step_label = f"move_{Pi}_{move_type}"

        # print(start_point)

        nn = 0 if move_type == 'horizontal' else 1
        offset = start_point[nn]
        direction=+1
        pos_to_freq_func = get_pos_to_freq_func(move_type)

        duration = move_duration
        num_samples = int(np.round(duration * sample_rate / 4096) * 4096) + 4096
        duration = num_samples / sample_rate
        dtt = np.linspace(0, duration, num_samples, endpoint=False)

        if move_type in ['horizontal', 'vertical']:
            samples, cut_len = generate_samples(schedule, dtt, duration, cutting, pos_to_freq_func, move_type, direction, offset, linear_ramp=True)
            axis = Horizontal if move_type == 'horizontal' else Vertical

            axis.pass_sample(tt, samples, step_label)

            static_axis = Vertical if move_type == 'horizontal' else Horizontal
            static_coord = start_point[1]  if move_type == 'horizontal' else start_point[0]
            freq = Ver_position_to_frequency(static_coord) if move_type == 'horizontal' else Hor_position_to_frequency(static_coord)

            sample_static = standing_wave_inverse_gaussian('vertical' if move_type == 'horizontal' else 'horizontal',[freq], num_samples, duration)
            if cutting:
                sample_static[-cut_len:] = 0
            static_axis.pass_sample(tt, sample_static, step_label)   

        return move_duration*usec

    def all_moves_loading(tt):
        """
        Generate all possible moves for the tweezers. 
        """
        for move in edges_list:
            tt += movingTweezer(tt, move[0], move[1], linear_ramp=False)
            tt+=dt
            tt += movingTweezer(tt, move[1], move[0], linear_ramp=False)
            tt+=dt
        return tt
        


if False: #Envelope of ttl and analog

    def TABLE_MODE_ON(channel_name, tt): 
        
        trigger_name = channel_name+'_trigger'
        channel_trigger = globals().get(trigger_name)

        channel_trigger.go_high(tt)
        channel_trigger.go_low(tt+dt)

    def TABLE_MODE_OFF(channel_name, tt): 

        channel = globals().get(channel_name)
        channel.DDS.setamp(tt, 0e2)
        channel.DDS.setfreq(tt, 10e3)
    
        trigger_name = channel_name+'_trigger'
        channel_trigger = globals().get(trigger_name)

        channel_trigger.go_high(tt)
        channel_trigger.go_low(tt+dt)

    def NEW_TABLE_LINE(channel_name, tt, frequency, amplitude):

        channel = globals().get(channel_name)
        channel.DDS.setamp(tt, amplitude*1e2)
        channel.DDS.setfreq(tt, frequency*1e3)

        trigger_name = channel_name+'_trigger'
        channel_trigger = globals().get(trigger_name)

        channel_trigger.go_high(tt)
        channel_trigger.go_low(tt+dt)

    def MOT_Blue2D_AOM_TTL(tt, control=True):
        if control:
            dueD_MOT_gate.go_high(tt) #QRF MOGLABS
        else:
            dueD_MOT_gate.go_low(tt)
    
    def MOT_Blue3D_AOM_TTL(tt, control=True):
        if control:
            treD_MOT_gate.go_high(tt) #QRF MOGLABS
        else:
            treD_MOT_gate.go_low(tt)
    
    def MOT_Blue3D_AOM_freq(tt, value):
        return
    
    def MOT_Blue3D_AOM_power(tt, value):
        return

    def MOT_Red3D_AOM_TTL(tt, control=True):
        if control:
            RedMOT_gate.go_high(tt)  #QRF MOGLABS
        else:
            RedMOT_gate.go_low(tt) 

    def MOT_Red3D_Switch_TTL(tt, control=True):
        if control:
            Red_commonSwitch.go_high(tt) #RF switch
        else:
            Red_commonSwitch.go_low(tt) 

    def MOT_Red3D_multiFrq_TTL(tt, control=True):
        if control:
            Red_multiFrq.go_high(tt) 
        else:
            Red_multiFrq.go_low(tt) 

    def MOT_Red3D_singleFrq_TTL(tt, control=True):
        if control:
            Red_singleFrq.go_high(tt)
        else:
            Red_singleFrq.go_low(tt) 

    def Sisyphus_AOM_TTL(tt, control=True):
        if control:
            Sisyphus_gate.go_high(tt)
        else:
            Sisyphus_gate.go_low(tt)

    def BlueImaging_AOM_TTL(tt, control=True):
        if control:
            ImagingBeam_gate.go_high(tt)
        else:
            ImagingBeam_gate.go_low(tt)

    def BlueImagingTweez_AOM_TTL(tt, control=True):
        if control:
            ImagingTweezBeam_gate.go_high(tt)
        else:
            ImagingTweezBeam_gate.go_low(tt)        

    def Twizzi_Switch_TTL(tt, control=True):
        if control:
            Tweezer_switch.go_high(tt)
        else:
            Tweezer_switch.go_low(tt)

    def Tweezers_AOM_TTL(tt, control=True):
        if control:
            Tweezers_gate.go_high(tt)
        else:
            Tweezers_gate.go_low(tt)  

    def MOT_Blue3D_Shutter_TTL(tt, control=True):
        if control:
            Shutter_Blue.go_high(tt)
        else:
            Shutter_Blue.go_low(tt)

    def COILSmain_SwitchON_TTL(tt, control=True):
        if control:
            IGBT_close.go_high(tt)
        else:
            IGBT_close.go_low(tt)

    def COILSmain_Config(tt, type):
        if type=='H':
            return
        elif type=='AH':
            return
        else:
            print('Value not allowed.')

    def COILSmain_Current(tt, value=0):
        BigCoilsI.constant(tt, abs(value))

    def COILSmain_Voltage(tt, value=0):
        BigCoilsV.constant(tt, abs(value))

    def COILScompX_Current(tt, value=0):
        CompCoilsI_X.constant(tt, abs(value))

    def COILScompY_Current(tt, value=0):
        CompCoilsI_Y.constant(tt, abs(value))

    def COILScompZ_Current(tt, value=0):
        CompCoilsI_Z.constant(tt, abs(value))

    def COILScomp_SwitchON_TTL(tt, control=True):
        if control:
            coilsMosfet.go_high(tt+dt)
        else:
            coilsMosfet.go_low(tt+dt)

    def Current_span(coils, tt, Final_V, Initial_V):
        n_step=round(Final_V-Initial_V/0.001)
        if n_step>0:
            for i in range(0,n_step):
                coils.constant(tt, GLOBALS['Z_Coils_Current']+i*0.001)
                tt+=100*usec
                return tt
        else:
            step_n=-n_step
            for i in range(0,step_n):
                coils.constant(tt, GLOBALS['Z_Coils_Current']-i*0.001)  
                tt+=100*usec
                return tt 

if False:
    def BlueMot_load(tt, load_time):
        tt+=dt        
        COILSmain_SwitchON_TTL(tt, True)
        tt+=dt
        MOT_Blue3D_Shutter_TTL(tt, False)
        tt+=2*msec
        MOT_Blue3D_AOM_TTL(tt, False)

        COILSmain_Current(tt, GLOBALS['coils_current_cntrl'])
        tt+=dt
        COILSmain_Voltage(tt, 5)
        tt+=dt

        MOT_Blue2D_AOM_TTL(tt, True)
        MOT_Blue3D_AOM_TTL(tt, True)
        tt+=load_time
        return tt
    
    def BlueMot_load_Table(tt, load_time):
        tt+=dt        
        COILSmain_SwitchON_TTL(tt, True)
        tt+=dt
        MOT_Blue3D_Shutter_TTL(tt, False)
        tt+=2*msec
        # TABLE_MODE_OFF('treD_MOT', tt)
        # tt+=20*usec

        COILSmain_Current(tt, GLOBALS['coils_current_cntrl'])
        tt+=dt
        COILSmain_Voltage(tt, 5)
        tt+=dt

        MOT_Blue2D_AOM_TTL(tt, True)

        NEW_TABLE_LINE('treD_MOT', tt, GLOBALS['treD_MOT_Frq']/1e6, GLOBALS['treD_MOT_Pow'])

        tt+=load_time
        return tt

    def BlueMot_off_Table(tt):
        MOT_Blue2D_AOM_TTL(tt-GLOBALS['TwoD_DELAY']+dt, False)
        TABLE_MODE_OFF('treD_MOT', tt)
        tt+=2*usec
        tt+=dt
        MOT_Blue3D_Shutter_TTL(tt-1*msec, True)

        tt+=dt
        COILSmain_Current(tt,0)
        tt+=1*usec
        COILSmain_SwitchON_TTL(tt, False)
        tt+=dt

        return tt

    def BlueMot_off(tt):
        MOT_Blue2D_AOM_TTL(tt-GLOBALS['TwoD_DELAY']+dt, False)
        MOT_Blue3D_AOM_TTL(tt, False)
        tt+=dt
        MOT_Blue3D_Shutter_TTL(tt-1*msec, True)

        tt+=dt
        COILSmain_Current(tt,0)
        tt+=1*usec
        COILSmain_SwitchON_TTL(tt, False)
        tt+=dt

        return tt

    def BlueMot(tt, loading_time):
        tt=BlueMot_load(tt, loading_time)
        tt=BlueMot_off(tt)
        return tt

    def BlueMot_Table(tt, loading_time):
        tt=BlueMot_load_Table(tt, loading_time)
        tt=BlueMot_off_Table(tt)
        return tt

    def BlueMOT_molass(tt, loading_time, T_BlueMolass):
        #MOT
        tt=BlueMot_load(tt, loading_time)
        MOT_Blue2D_AOM_TTL(tt-GLOBALS['TwoD_DELAY']+dt, False)

        tt+=dt
        COILSmain_Current(tt,0)
        tt+=1*usec
        COILSmain_SwitchON_TTL(tt, False)
        tt+=dt

        #MOLASS
        tt+=T_BlueMolass

        MOT_Blue3D_AOM_TTL(tt, False)
        tt+=dt
        COILSmain_SwitchON_TTL(tt-2*msec, True)
        MOT_Blue3D_AOM_TTL(tt+20*msec, False)

        return tt

    def RedMot_on(tt):
        tt+=dt
        MOT_Red3D_AOM_TTL(tt, True)
        tt+=dt
        return tt

    def RedMot_off(tt):
        tt+=dt
        MOT_Red3D_AOM_TTL(tt, False)
        tt+=dt
        return tt

    def RedMot(tt, duration_wait):
        tt=RedMot_on(tt)
        tt=RedMot_off(tt+duration_wait)
        return tt

    def RedMot_on_multifrq(tt):
        tt+=dt
        MOT_Red3D_multiFrq_TTL(tt, True) 
        tt+=dt
        return tt

    def RedMot_off_multifrq(tt):
        tt+=dt
        MOT_Red3D_multiFrq_TTL(tt, False) 
        tt+=dt
        return tt

    def RedMot_multifrq(tt, duration_wait):
        
        MOT_Red3D_Switch_TTL(tt, True)
        tt+=dt
        tt=RedMot_on_multifrq(tt)
        tt=RedMot_off_multifrq(tt+duration_wait)
        MOT_Red3D_Switch_TTL(tt, False)
        
        return tt

    def Red_Mot_Luca(tt, red_duration, blue_duration, shield):

        MOT_Red3D_Switch_TTL(tt, True)      #Global rf switch
        tt+=dt

        if shield:
            MOT_Red3D_AOM_TTL(tt, True)     
            tt+=dt
            MOT_Red3D_multiFrq_TTL(tt, False) 
            MOT_Red3D_singleFrq_TTL(tt, True) 

        tt=BlueMot_load(tt, blue_duration)       #Blue mot loading

        MOT_Blue2D_AOM_TTL(tt-GLOBALS['TwoD_DELAY']+dt, False)
        MOT_Blue3D_AOM_TTL(tt, False)
        tt+=dt
        MOT_Blue3D_Shutter_TTL(tt-1*msec, True)

    ##### RED MOT SECTION

        MOT_Red3D_AOM_TTL(tt, False)        #Luca moved this part here to turn on the comb even during the switching off
        tt+=dt
        MOT_Red3D_singleFrq_TTL(tt, False) 
        tt+=dt
        MOT_Red3D_multiFrq_TTL(tt, True)

        tt+=red_duration

        COILSmain_Current(tt, 0)
        tt+=1*usec
        COILSmain_SwitchON_TTL(tt, False)
        tt+=dt

        MOT_Red3D_Switch_TTL(tt, False)       #Luca commented this part to use the4 function in RED_MOT_Salvi
        MOT_Red3D_multiFrq_TTL(tt, False)          

        return tt

    def RedBroad_Mot(tt, red_duration, blue_duration, shield, shieldMulti):

        MOT_Red3D_Switch_TTL(tt, True)      #Global rf switch
        tt+=dt

        if shield:
            MOT_Red3D_AOM_TTL(tt, True)     
            tt+=dt
            MOT_Red3D_multiFrq_TTL(tt, False) 
            MOT_Red3D_singleFrq_TTL(tt, True) 

        if shieldMulti:
            MOT_Red3D_AOM_TTL(tt, False)     
            tt+=dt
            MOT_Red3D_multiFrq_TTL(tt, True) 
            MOT_Red3D_singleFrq_TTL(tt, False) 

        tt=BlueMot(tt, blue_duration)       #Blue mot loading

    ##### RED MOT SECTION

        MOT_Red3D_AOM_TTL(tt, False)        #Luca moved this part here to turn on the comb even during the switching off
        tt+=dt
        MOT_Red3D_singleFrq_TTL(tt, False) 
        tt+=dt
        MOT_Red3D_multiFrq_TTL(tt, True)

        #IGBT_close.go_high(tt)
        tt+=400*usec
        IGBT_close.go_high(tt)
        tt+=dt
        COILSmain_Current(tt, GLOBALS['coils_current_ctrl_red'])          #Turn on the COILSmain at 10 A, roughly 5 G/cm
        tt+=dt
        COILSmain_Voltage(tt, 0.8)
        tt+=dt

        ## tt+=300*us
        # MOT_Red3D_AOM_TTL(tt, False)
        # tt+=dt
        # MOT_Red3D_singleFrq_TTL(tt, False) 
        # tt+=dt
        # MOT_Red3D_multiFrq_TTL(tt, True)

        tt+=red_duration

        tt+=dt
        COILSmain_Current(tt, 0)
        tt+=1*usec
        COILSmain_SwitchON_TTL(tt, False)
        tt+=dt

        MOT_Red3D_Switch_TTL(tt, False)       #Luca commented this part to use the4 function in RED_MOT_Salvi
        MOT_Red3D_multiFrq_TTL(tt, False)          

        return tt

    def RedBroad_Mot_Final(tt, red_duration, blue_duration, shield, shieldMulti):

        MOT_Red3D_Switch_TTL(tt, True)      #Global rf switch
        tt+=dt

        if shield:
            MOT_Red3D_AOM_TTL(tt, True)     
            tt+=dt
            MOT_Red3D_multiFrq_TTL(tt, False) 
            MOT_Red3D_singleFrq_TTL(tt, True) 

        if shieldMulti:
            MOT_Red3D_AOM_TTL(tt, False)     
            tt+=dt
            MOT_Red3D_multiFrq_TTL(tt, True) 
            MOT_Red3D_singleFrq_TTL(tt, False) 

        tt=BlueMot_load(tt, blue_duration)

        MOT_Blue2D_AOM_TTL(tt-GLOBALS['TwoD_DELAY']+dt, False)
        MOT_Blue3D_AOM_TTL(tt, False)
        tt+=dt
        MOT_Blue3D_Shutter_TTL(tt-1*msec, True)

        tt+=dt
        COILSmain_Voltage(tt, 0)
        tt+=dt
        COILSmain_Current(tt,0)
        tt+=1*usec
        COILSmain_SwitchON_TTL(tt, False)
        tt+=dt

        # tt+=dt
        # COILSmain_Current(tt,GLOBALS['coils_current_ctrl_red'])
        tt+=dt

    ##### RED MOT SECTION

        MOT_Red3D_AOM_TTL(tt, False)        #Luca moved this part here to turn on the comb even during the switching off
        tt+=dt
        MOT_Red3D_singleFrq_TTL(tt, False) 
        tt+=dt
        MOT_Red3D_multiFrq_TTL(tt, True)

        #IGBT_close.go_high(tt)
        tt+=300*usec
        IGBT_close.go_high(tt)
        tt+=dt
        COILSmain_Voltage(tt, 0.4)
        tt+=dt
        COILSmain_Current(tt, GLOBALS['coils_current_ctrl_red'])          #Turn on the COILSmain at 10 A, roughly 5 G/cm
        tt+=dt


        ## tt+=300*us
        # MOT_Red3D_AOM_TTL(tt, False)
        # tt+=dt
        # MOT_Red3D_singleFrq_TTL(tt, False) 
        # tt+=dt
        # MOT_Red3D_multiFrq_TTL(tt, True)

        tt+=red_duration

        tt+=dt
        COILSmain_Current(tt, 0)
        tt+=1*usec
        COILSmain_SwitchON_TTL(tt, False)
        tt+=dt

        MOT_Red3D_Switch_TTL(tt, False)       #Luca commented this part to use the4 function in RED_MOT_Salvi
        MOT_Red3D_multiFrq_TTL(tt, False)          

        return tt

    def RedBroad_Mot_Test(tt, red_duration, blue_duration, shield, shieldMulti):

        MOT_Red3D_Switch_TTL(tt, True)      #Global rf switch
        tt+=dt

        if shield:
            MOT_Red3D_AOM_TTL(tt, True)     
            tt+=dt
            MOT_Red3D_multiFrq_TTL(tt, False) 
            MOT_Red3D_singleFrq_TTL(tt, True) 

        if shieldMulti:
            MOT_Red3D_AOM_TTL(tt, False)     
            tt+=dt
            MOT_Red3D_multiFrq_TTL(tt, True) 
            MOT_Red3D_singleFrq_TTL(tt, False) 

        tt=BlueMot_load(tt, blue_duration)

        MOT_Blue2D_AOM_TTL(tt-GLOBALS['TwoD_DELAY']+dt, False)
        MOT_Blue3D_AOM_TTL(tt, False)
        tt+=dt
        MOT_Blue3D_Shutter_TTL(tt-1*msec, True)

        # treD_MOT.DDS.setamp(tt, GLOBALS['treD_MOT_Pow']*1e2/10)

        tt+=dt
        COILSmain_Voltage(tt, 0)
        tt+=dt
        COILSmain_Current(tt,0)
        tt+=1*usec
        COILSmain_SwitchON_TTL(tt, False)
        tt+=dt

        # tt+=dt
        # COILSmain_Current(tt,GLOBALS['coils_current_ctrl_red'])
        tt+=dt

    ##### RED MOT SECTION

        MOT_Red3D_AOM_TTL(tt, False)        #Luca moved this part here to turn on the comb even during the switching off
        tt+=dt
        MOT_Red3D_singleFrq_TTL(tt, False) 
        tt+=dt
        MOT_Red3D_multiFrq_TTL(tt, True)

        tt+=300*usec
        COILSmain_SwitchON_TTL(tt, True)
        # IGBT_close.go_high(tt)
        tt+=dt
        COILSmain_Voltage(tt, 0.4)
        tt+=dt
        COILSmain_Current(tt, GLOBALS['coils_current_ctrl_red'])          #Turn on the COILSmain at 10 A, roughly 5 G/cm


        ## tt+=300*us
        # MOT_Red3D_AOM_TTL(tt, False)
        # tt+=dt
        # MOT_Red3D_singleFrq_TTL(tt, False) 
        # tt+=dt
        # MOT_Red3D_multiFrq_TTL(tt, True)

        tt+=red_duration/2

        # COILSmain_Current(tt, GLOBALS['coils_current_ctrl_red']*0.2)
        # tt+=red_duration/2
        # COILSmain_Current(tt, GLOBALS['coils_current_ctrl_red']*0.4)          #Increases the gradient gradually
        # tt+=red_duration/8
        # COILSmain_Current(tt, GLOBALS['coils_current_ctrl_red']*0.6)          
        # tt+=red_duration/8
        # COILSmain_Current(tt, GLOBALS['coils_current_ctrl_red']*0.8)          
        # tt+=red_duration/8
        # COILSmain_Current(tt, GLOBALS['coils_current_ctrl_red']*1)          
        # tt+=red_duration/8

        # COILScompZ_Current(tt, GLOBALS['coils_current_ctrl_red']*1.00001)
        # tt+=red_duration/4
        # COILScompZ_Current(tt, GLOBALS['coils_current_ctrl_red']*1.00002)
        # tt+=red_duration/4
        # COILScompZ_Current(tt, GLOBALS['coils_current_ctrl_red']*1.15)
        # tt+=red_duration/4
        # COILScompZ_Current(tt, GLOBALS['coils_current_ctrl_red']*1.2)
        tt+=red_duration/4

        tt+=dt

        MOT_Red3D_multiFrq_TTL(tt, False)
        tt+=dt
        MOT_Red3D_AOM_TTL(tt, True)        #Single frequency mot
        tt+=dt
        MOT_Red3D_singleFrq_TTL(tt, True)     
        tt+=red_duration/12


        tt+=dt
        COILSmain_Current(tt, 0)
        tt+=1*usec
        COILSmain_SwitchON_TTL(tt, False)
        tt+=dt

        MOT_Red3D_Switch_TTL(tt, False)       #Luca commented this part to use the4 function in RED_MOT_Salvi
        MOT_Red3D_singleFrq_TTL(tt, False)
        # MOT_Red3D_multiFrq_TTL(tt, False)          


        return tt

    def RedMot_single(tt, red_duration, blue_duration, shield, shieldMulti):

        MOT_Red3D_Switch_TTL(tt, True)      #Global rf switch
        tt+=dt

        if shield:
            MOT_Red3D_AOM_TTL(tt, True)     
            tt+=dt
            MOT_Red3D_multiFrq_TTL(tt, False) 
            MOT_Red3D_singleFrq_TTL(tt, True) 

        if shieldMulti:
            MOT_Red3D_AOM_TTL(tt, False)     
            tt+=dt
            MOT_Red3D_multiFrq_TTL(tt, True) 
            MOT_Red3D_singleFrq_TTL(tt, False) 

        tt=BlueMot_load(tt, blue_duration)

        MOT_Blue2D_AOM_TTL(tt-GLOBALS['TwoD_DELAY']+dt, False)
        MOT_Blue3D_AOM_TTL(tt, False)
        tt+=dt
        MOT_Blue3D_Shutter_TTL(tt-1*msec, True)

        # treD_MOT.DDS.setamp(tt, GLOBALS['treD_MOT_Pow']*1e2/10)

        tt+=dt
        COILSmain_Voltage(tt, 0)
        tt+=dt
        COILSmain_Current(tt,0)
        tt+=1*usec
        COILSmain_SwitchON_TTL(tt, False)
        tt+=dt

        # tt+=dt
        # COILSmain_Current(tt,GLOBALS['coils_current_ctrl_red'])
        tt+=dt

    ##### RED MOT SECTION

        MOT_Red3D_AOM_TTL(tt, False)        #Luca moved this part here to turn on the comb even during the switching off
        tt+=dt
        MOT_Red3D_singleFrq_TTL(tt, False) 
        tt+=dt
        MOT_Red3D_multiFrq_TTL(tt, True)

        tt+=300*usec
        COILSmain_SwitchON_TTL(tt, True)
        # IGBT_close.go_high(tt)
        tt+=dt
        COILSmain_Voltage(tt, 0.4)
        tt+=dt
        COILSmain_Current(tt, GLOBALS['coils_current_ctrl_red'])          #Turn on the COILSmain at 10 A, roughly 5 G/cm


        ## tt+=300*us
        # MOT_Red3D_AOM_TTL(tt, False)
        # tt+=dt
        # MOT_Red3D_singleFrq_TTL(tt, False) 
        # tt+=dt
        # MOT_Red3D_multiFrq_TTL(tt, True)

        tt+=red_duration/2

        # COILSmain_Current(tt, GLOBALS['coils_current_ctrl_red']*0.2)
        # tt+=red_duration/2
        # COILSmain_Current(tt, GLOBALS['coils_current_ctrl_red']*0.4)          #Increases the gradient gradually
        # tt+=red_duration/8
        # COILSmain_Current(tt, GLOBALS['coils_current_ctrl_red']*0.6)          
        # tt+=red_duration/8
        # COILSmain_Current(tt, GLOBALS['coils_current_ctrl_red']*0.8)          
        # tt+=red_duration/8
        # COILSmain_Current(tt, GLOBALS['coils_current_ctrl_red']*1)          
        # tt+=red_duration/8

        # COILScompZ_Current(tt, GLOBALS['coils_current_ctrl_red']*1.00001)
        # tt+=red_duration/4
        # COILScompZ_Current(tt, GLOBALS['coils_current_ctrl_red']*1.00002)
        # tt+=red_duration/4
        # COILScompZ_Current(tt, GLOBALS['coils_current_ctrl_red']*1.15)
        # tt+=red_duration/4
        # COILScompZ_Current(tt, GLOBALS['coils_current_ctrl_red']*1.2)
        tt+=red_duration/4

        tt+=dt

        MOT_Red3D_multiFrq_TTL(tt, False)
        tt+=dt
        MOT_Red3D_AOM_TTL(tt, True)        #Single frequency mot
        tt+=dt
        MOT_Red3D_singleFrq_TTL(tt, True)     
        tt+=red_duration/4


        tt+=dt
        COILSmain_Current(tt, 0)
        tt+=1*usec
        COILSmain_SwitchON_TTL(tt, False)
        tt+=dt

        MOT_Red3D_Switch_TTL(tt, False)       #Luca commented this part to use the4 function in RED_MOT_Salvi
        MOT_Red3D_singleFrq_TTL(tt, False)
        # MOT_Red3D_multiFrq_TTL(tt, False)          


        return tt

    def RedMot_singleTable(tt, red_duration, blue_duration, shield, shieldMulti):

        MOT_Red3D_Switch_TTL(tt, True)      #Global rf switch
        tt+=dt

        if shield:
            MOT_Red3D_AOM_TTL(tt, True)     
            tt+=dt
            MOT_Red3D_multiFrq_TTL(tt, False) 
            MOT_Red3D_singleFrq_TTL(tt, True) 

        if shieldMulti:
            MOT_Red3D_AOM_TTL(tt, False)     
            tt+=dt
            MOT_Red3D_multiFrq_TTL(tt, True) 
            MOT_Red3D_singleFrq_TTL(tt, False) 

        tt=BlueMot_load(tt, blue_duration)

        MOT_Blue2D_AOM_TTL(tt-GLOBALS['TwoD_DELAY']+dt, False)
        MOT_Blue3D_AOM_TTL(tt, False)
        tt+=dt
        MOT_Blue3D_Shutter_TTL(tt-1*msec, True)

        # treD_MOT.DDS.setamp(tt, GLOBALS['treD_MOT_Pow']*1e2/10)

        tt+=dt
        COILSmain_Voltage(tt, 0)
        tt+=dt
        COILSmain_Current(tt,0)
        tt+=1*usec
        COILSmain_SwitchON_TTL(tt, False)
        tt+=dt

        # tt+=dt
        # COILSmain_Current(tt,GLOBALS['coils_current_ctrl_red'])
        tt+=dt

    ##### RED MOT SECTION

        MOT_Red3D_AOM_TTL(tt, False)        #Luca moved this part here to turn on the comb even during the switching off
        tt+=dt
        MOT_Red3D_singleFrq_TTL(tt, False) 
        tt+=dt
        MOT_Red3D_multiFrq_TTL(tt, True)

        tt+=300*usec
        COILSmain_SwitchON_TTL(tt, True)
        # IGBT_close.go_high(tt)
        tt+=dt
        COILSmain_Voltage(tt, 0.4)
        tt+=dt
        COILSmain_Current(tt, GLOBALS['coils_current_ctrl_red'])          #Turn on the COILSmain at 10 A, roughly 5 G/cm


        tt+=red_duration

        tt+=dt

        MOT_Red3D_multiFrq_TTL(tt, False)
        tt+=dt
        # MOT_Red3D_AOM_TTL(tt, True)        #Single frequency mot
        NEW_TABLE_LINE('RedMOT', tt, GLOBALS['Red_MOT_Frq']/1e6, GLOBALS['Red_MOT_Pow'])
        tt+=3*dt
        MOT_Red3D_singleFrq_TTL(tt, True)     


        tt+=red_duration/4

        # COILSmain_Current(tt, GLOBALS['coils_current_ctrl_red']*1.2)  
        # tt+=dt
        # NEW_TABLE_LINE('RedMOT', tt, GLOBALS['Red_MOT_Frq']/1e6, GLOBALS['Red_MOT_Pow'])
        # NEW_TABLE_LINE('RedMOT', tt, 75.455, 21.5)
        # tt+=3*dt
        
        # tt+=3*dt

        # tt+=red_duration

        # NEW_TABLE_LINE('RedMOT', tt, 75.455, 20)
        # COILSmain_Current(tt, GLOBALS['coils_current_ctrl_red'])  
        # tt+=3*dt

        # tt+=red_duration/8

        # NEW_TABLE_LINE('RedMOT', tt, 75.455, 18.5)
        # COILSmain_Current(tt, GLOBALS['coils_current_ctrl_red'])  
        # tt+=3*dt

        # tt+=red_duration/8
        # tt+=3*dt
        COILSmain_Current(tt, 0)
        tt+=1*usec
        COILSmain_SwitchON_TTL(tt, False)
        tt+=dt

        MOT_Red3D_Switch_TTL(tt, False)       
        MOT_Red3D_singleFrq_TTL(tt, False)
            
        return tt

    def RedBroad_Mot_Table(tt, red_duration, blue_duration, shield, shieldMulti):

        MOT_Red3D_Switch_TTL(tt, True)      #Global rf switch
        tt+=5*msec

        if shield:
            MOT_Red3D_AOM_TTL(tt, True)     
            tt+=dt
            MOT_Red3D_multiFrq_TTL(tt, False) 
            MOT_Red3D_singleFrq_TTL(tt, True) 
        elif shieldMulti:
            MOT_Red3D_AOM_TTL(tt, False)     
            tt+=dt
            MOT_Red3D_multiFrq_TTL(tt, True) 
            MOT_Red3D_singleFrq_TTL(tt, False) 


        tt=BlueMot_load_Table(tt, blue_duration)

        ### Blue MOT OFF
        MOT_Blue2D_AOM_TTL(tt-GLOBALS['TwoD_DELAY']+dt, False)
        TABLE_MODE_OFF('treD_MOT',tt) 
        tt+=2*usec
        tt+=dt
        MOT_Blue3D_Shutter_TTL(tt-1*msec, True)
        
        tt+=dt
        COILSmain_Voltage(tt, 0)
        tt+=dt
        COILSmain_Current(tt,0)
        tt+=1*usec
        COILSmain_SwitchON_TTL(tt, False)
        tt+=dt


    #### RED MOT SECTION
    
        MOT_Red3D_AOM_TTL(tt, False)        #Luca moved this part here to turn on the comb even during the switching off
        tt+=dt
        MOT_Red3D_singleFrq_TTL(tt, False) 
        tt+=dt
        MOT_Red3D_multiFrq_TTL(tt, True)

        tt+=300*usec
        COILSmain_SwitchON_TTL(tt, True)
        # IGBT_close.go_high(tt)
        tt+=dt
        COILSmain_Voltage(tt, 0.4)
        tt+=dt
        COILSmain_Current(tt, GLOBALS['coils_current_ctrl_red'])          #Turn on the COILSmain at 10 A, roughly 5 G/cm


        tt+=red_duration/2

        tt+=red_duration/4

        tt+=dt

        MOT_Red3D_multiFrq_TTL(tt, False)
        tt+=dt
        MOT_Red3D_AOM_TTL(tt, True)        #Single frequency mot
        tt+=dt
        MOT_Red3D_singleFrq_TTL(tt, True)     
        tt+=red_duration/4


        tt+=dt
        COILSmain_Current(tt, 0)
        tt+=1*usec
        COILSmain_SwitchON_TTL(tt, False)
        tt+=dt

        MOT_Red3D_Switch_TTL(tt, False)       #Luca commented this part to use the4 function in RED_MOT_Salvi
        MOT_Red3D_singleFrq_TTL(tt, False)
        # MOT_Red3D_multiFrq_TTL(tt, False)          


        return tt

    def take_absorbImaging(tt, beam_duration):
        trigger_delay=100*usec+5*usec #100 for camera activation + 5 as safety buffer
        Basler_Camera_abs_readout=4*120*msec # was at 120ms with small ROI, when enlarged changed to 200ms, still had issues capturing, changed to 480 and no issue

        BlueImaging_AOM_TTL(tt, True)
        BlueImaging_AOM_TTL(tt+beam_duration, False)
        tt+=Basler_Camera_abs.expose(tt-trigger_delay,'Atoms', frametype='tiff')
        
        tt+=Basler_Camera_abs_readout 

        BlueImaging_AOM_TTL(tt, True)
        BlueImaging_AOM_TTL(tt+beam_duration, False)
        tt+=Basler_Camera_abs.expose(tt-trigger_delay,'Probe', frametype='tiff')

        tt+=Basler_Camera_abs_readout 

        Basler_Camera_abs.expose(tt-trigger_delay,'Background', frametype='tiff')

        tt+=Basler_Camera_abs_readout 

        return tt

    def take_absorbImaging_test(tt, beam_duration):
        trigger_delay=100*usec+5*usec #100 for camera activation + 5 as safety buffer
        Basler_Camera_abs_readout=120*msec # was at 120ms, changed to 200ms, still had issues capturing, changed to 300 and no issue

        MOT_Blue2D_AOM_TTL(tt, True)
        MOT_Blue2D_AOM_TTL(tt+beam_duration, False)
        tt+=Basler_Camera_abs.expose(tt-trigger_delay,'Atoms', frametype='tiff')
        
        tt+=4*Basler_Camera_abs_readout 

        MOT_Blue2D_AOM_TTL(tt, True)
        MOT_Blue2D_AOM_TTL(tt+beam_duration, False)
        tt+=Basler_Camera_abs.expose(tt-trigger_delay,'Probe', frametype='tiff')

        tt+=4*Basler_Camera_abs_readout 

        Basler_Camera_abs.expose(tt-trigger_delay,'Background', frametype='tiff')

        tt+=10*Basler_Camera_abs_readout 

        return tt

    def do_Twizzi(tt, Tweezer_duration):
        Twizzi_Switch_TTL(tt, True)
        tt+=Tweezer_duration
        Twizzi_Switch_TTL(tt, False)
        return tt
        
    def take_fluoImaging_Andor(tt, name):

        BlueImaging_AOM_TTL(tt+10*usec, True)
        tt+=Andor_Camera.expose(tt, str(name), frametype='tiff') 
        BlueImaging_AOM_TTL(tt, False)
        return tt

    def take_fluoImaging_Basler(tt, name):
        trigger_delay=100*usec+5*usec
        tt+=Basler_Camera_abs.expose(tt-trigger_delay,name, frametype='tiff')
        return tt

    def set_MOGLABS_ready(tt):
        G_Imaging_Frq=GLOBALS['Imaging_Frq']/1e6
        G_ImagingFluo_Frq=GLOBALS['ImagingFluo_Frq']/1e6
        G_dueD_MOT_Frq=GLOBALS['dueD_MOT_Frq']/1e6
        G_treD_MOT_Frq=GLOBALS['treD_MOT_Frq']/1e6
        G_Red_MOT_Frq=GLOBALS['Red_MOT_Frq']/1e6
        G_ImagingTweez_Frq=GLOBALS['ImagingTweez_Frq']/1e6
        G_Sisyphus_Frq=GLOBALS['Sisyphus_Frq']/1e6
        G_Tweezers_Frq=GLOBALS['Tweezers_Frq']/1e6
            
        G_Imaging_Pow=GLOBALS['Imaging_Pow']
        G_ImagingFluo_Pow=GLOBALS['ImagingFluo_Pow']
        G_treD_MOT_Pow=GLOBALS['treD_MOT_Pow']
        G_Red_MOT_Pow=GLOBALS['Red_MOT_Pow']
        G_ImagingTweez_Pow=GLOBALS['ImagingTweez_Pow']
        G_dueD_MOT_Pow=GLOBALS['dueD_MOT_Pow']    
        G_Sisyphus_Pow=GLOBALS['Sisyphus_Pow']
        G_Tweezers_Pow=GLOBALS['Tweezers_Pow']

        # RedMOT.DDS.setfreq(tt, G_Red_MOT_Frq*1e3)  ##################### VERY VERY  BAD THINGS TO CIRCUMVENT DRIVER BUG  TODO: FIX removing 1e3or2 ask Andre #################
        # RedMOT.DDS.setamp(tt, G_Red_MOT_Pow*1e2)

        # ImagingBeam.DDS.setfreq(tt, G_Imaging_Frq*1e3)
        # ImagingBeam.DDS.setamp(tt, G_Imaging_Pow*1e2)

        dueD_MOT.DDS.setfreq(tt, G_dueD_MOT_Frq*1e3)
        dueD_MOT.DDS.setamp(tt, G_dueD_MOT_Pow*1e2)

        treD_MOT.DDS.setfreq(tt, G_treD_MOT_Frq*1e3)
        treD_MOT.DDS.setamp(tt, G_treD_MOT_Pow*1e2)

        ImagingTweezBeam.DDS.setfreq(tt, G_ImagingTweez_Frq*1e3)
        ImagingTweezBeam.DDS.setamp(tt, G_ImagingTweez_Pow*1e2)

        Sisyphus.DDS.setfreq(tt, G_Sisyphus_Frq*1e3)
        Sisyphus.DDS.setamp(tt, G_Sisyphus_Pow*1e2)

        Tweezers.DDS.setfreq(tt,  G_Tweezers_Frq*1e3)
        Tweezers.DDS.setamp(tt, G_Tweezers_Pow*1e2)
        Tweezers_gate.go_high(tt+dt)

    def set_CompCoils(tt, control="ON"):
        if control=="ON":
            COILScomp_SwitchON_TTL(tt, True)
            tt+=5*usec
            COILScompX_Current(tt, abs(GLOBALS['X_Coils_Current']))
            COILScompY_Current(tt+dt, abs(GLOBALS['Y_Coils_Current']))
            COILScompZ_Current(tt+2*dt, abs(GLOBALS['Z_Coils_Current']))
        else:
            COILScomp_SwitchON_TTL(tt, False)
            tt+=5*usec
            COILScompX_Current(tt, 0)
            COILScompY_Current(tt+dt, 0)
            COILScompZ_Current(tt+2*dt, 0)
        return tt+3*dt

    def setoff_CompCoils(tt): ## OBSOLETE
        COILScomp_SwitchON_TTL(tt, False)
        tt+=5*usec
        CompCoilsI_X.constant(tt, 0)
        tt+=dt
        CompCoilsI_Y.constant(tt, 0)
        tt+=dt
        CompCoilsI_Z.constant(tt, 0)
        tt+=dt
        return tt 

    def analog_ramp(channel, tt, v_initial, v_final, duration, v_step_size=0.01):
        v_step_size=abs(v_step_size)
        n_step=abs(round((v_final-v_initial)/v_step_size))
        deltat=duration/n_step
        if v_final>v_initial:
            for i in range(0,n_step):
                channel.constant(tt, v_initial+i*v_step_size)
                tt+=deltat
        else:
            for i in range(0,n_step):
                channel.constant(tt, v_initial-i*v_step_size)
                tt+=deltat
        return tt 

    def set_CompCoils_QuantizationAxis(tt, control="ON", duration=GLOBALS['QuantizAxis_ramp_duration'], v_step_size=0.01):
        if control=="ON":
            analog_ramp(CompCoilsI_X, tt, abs(GLOBALS['X_Coils_Current']), abs(GLOBALS['QuantizAxis_X_Coils_Current']), duration, v_step_size)
            analog_ramp(CompCoilsI_Y, tt+dt, abs(GLOBALS['Y_Coils_Current']), abs(GLOBALS['QuantizAxis_Y_Coils_Current']), duration, v_step_size)
            analog_ramp(CompCoilsI_Z, tt+2*dt, abs(GLOBALS['Z_Coils_Current']), abs(GLOBALS['QuantizAxis_Z_Coils_Current']), duration, v_step_size)
        else:
            analog_ramp(CompCoilsI_X, tt, abs(GLOBALS['QuantizAxis_X_Coils_Current']), abs(GLOBALS['X_Coils_Current']), duration, v_step_size)
            analog_ramp(CompCoilsI_Y, tt+dt, abs(GLOBALS['QuantizAxis_Y_Coils_Current']), abs(GLOBALS['Y_Coils_Current']), duration, v_step_size)
            analog_ramp(CompCoilsI_Z, tt+2*dt, abs(GLOBALS['QuantizAxis_Z_Coils_Current']), abs(GLOBALS['Z_Coils_Current']), duration, v_step_size)
        return tt+duration+3*dt

    def set_CompCoils_QuantizationAxis_test(tt, control="ON", duration=GLOBALS['QuantizAxis_ramp_duration'], samplerate=1e5):
        # Ramp compensation coils to/from values that set Quantization axis for imaging
        ## def ramp(self, t, duration, initial, final, samplerate, units=None, truncation=1.):
        # generate_analog_samples
        if control=="ON":
            CompCoilsI_X.ramp(tt,      duration, abs(GLOBALS['X_Coils_Current']), abs(GLOBALS['QuantizAxis_X_Coils_Current']), samplerate)
            CompCoilsI_Y.ramp(tt+dt,   duration, abs(GLOBALS['Y_Coils_Current']), abs(GLOBALS['QuantizAxis_Y_Coils_Current']), samplerate)
            CompCoilsI_Z.ramp(tt+2*dt, duration, abs(GLOBALS['Z_Coils_Current']), abs(GLOBALS['QuantizAxis_Z_Coils_Current']), samplerate)
        else:
            CompCoilsI_X.ramp(tt,      duration, abs(GLOBALS['QuantizAxis_X_Coils_Current']), abs(GLOBALS['X_Coils_Current']), samplerate)
            CompCoilsI_Y.ramp(tt+dt,   duration, abs(GLOBALS['QuantizAxis_Y_Coils_Current']), abs(GLOBALS['Y_Coils_Current']), samplerate)
            CompCoilsI_Z.ramp(tt+2*dt, duration, abs(GLOBALS['QuantizAxis_Z_Coils_Current']), abs(GLOBALS['Z_Coils_Current']), samplerate)
        return tt+duration+3*dt

    def fluo_resonant_Blue(tt):
        BlueImaging_AOM_TTL(tt+10*usec, True)
        exposure_time=10000*usec

        # tt-=100*msec ##############################################
        Andor_Camera_trigger.go_high(tt)
        # tt+=Andor_Camera.expose(tt+dt,'Fluo0', frametype='tiff') 
        tt+=10*usec   
        Andor_Camera_trigger.go_low(tt)
        # tt+=100*msec ##############################################

        tt+=exposure_time

        BlueImaging_AOM_TTL(tt, False)

        return tt

    def fluo_detuned_Blue(tt):
        BlueImagingTweez_AOM_TTL(tt+10*usec, True)
        exposure_time=10000*usec

        # tt-=100*msec ##############################################
        Andor_Camera_trigger.go_high(tt)
        # tt+=Andor_Camera.expose(tt+dt,'Fluo0', frametype='tiff') 
        tt+=10*usec   
        Andor_Camera_trigger.go_low(tt)
        # tt+=100*msec ##############################################

        tt+=exposure_time

        BlueImagingTweez_AOM_TTL(tt, False)

        return tt