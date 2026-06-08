########## ALL PATHS AWG CREATION #############
# by Andrea for Sr FloRydberg Group           #
# function to load all the possibile paths    #
# last edited 03/07/2024                      # 
###############################################
import numpy as np
import csv
from scipy.signal import hilbert
from PIL import Image
import os
import h5py
from labscript_utils import import_or_reload
import_or_reload('labscriptlib.Test_AWG_Spectrum.connection_table')
from labscriptlib.Test_AWG_Spectrum.connection_table import *

debugging_mode = False

def import_GLOBALS(shot_settings_path):
    GLOBALS = {}
    with h5py.File(shot_settings_path, 'r') as f:
        if 'globals' in f:
            for key in f['globals']:
                key_str = str(key)  # Ensure it's a string
                try:
                    value = f['globals'][key_str][()]
                except Exception as e:
                    print(f"Could not read key {key_str}: {e}")
                    continue

                # Optional: decode if it's a byte string
                if isinstance(value, bytes):
                    value = value.decode()

                try:
                    GLOBALS[key_str] = eval(value)
                except Exception:
                    GLOBALS[key_str] = value  # fallback to raw

    return GLOBALS


shot_settings_path='C:\\Experiments\\Test_AWG_Spectrum\\test.h5'
GLOBALS= import_GLOBALS(shot_settings_path)
print(GLOBALS)

if False: # === AWG Tweezer Embedding ===
    # TODO: take geometry from file

    # step_lenght = 2 * ranging /(grid_size - 1)

    # # print(step_lenght)

    # index = 0
    # for y in coords:
    #     for x in coords:
    #         points_dict[f'P{index}'] = (x, y)
    #         # print(f"({x},{y})")
    #         index += 1

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

    def start_reordering_sequence(tt):
        awg_trigger.go_high(tt)
        awg_trigger.go_low(tt + 10 * usec)

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

def all_paths(self, f):
    group = f[f"devices/{self.device_name}"]
    shot_seq_length=len(group['0'].attrs)
    last_index = shot_seq_length-1

    for index in range(shot_seq_length): #index of sequences
        index_h5 = str(index) # The index in the h5 file is a str
        instructions={}
        size=np.zeros(self.ch_num)
        for ch in self.channels:
            ### LOOP TROUGH STREAMING STEPS ###
            instructions[ch] = group[ch].attrs[index_h5]

            size[int(ch)]=instructions[ch]
        num_samples = int(max(size))

        data_combined= np.zeros(num_samples*self.ch_num, dtype=np.int16)

        instruction_label=group['0']["labels"].attrs[index_h5]
        print(instruction_label)

        instruction_hash = hash(instruction_label) # Generate the hash

        if instruction_hash in self.smart_cache:
            memory_index = self.smart_cache[instruction_hash]
            if debugging_mode:
                print(f'memory_index {memory_index}')
                print('already in memory')
        else:
            memory_index = len(self.smart_cache)
            if debugging_mode:
                print(f'memory_index {memory_index}')
                print('new in memory')
            self.smart_cache[instruction_hash] = memory_index
            # initial_values[memory_index] = ''
            for ch in self.channels:
                if debugging_mode:
                    print('channel '+str(ch))
                data = group[ch]["sample"].attrs[index_h5]
        
                # if index_h5 in group[ch]["labels"].attrs:
                #     initial_values[memory_index] = group[ch]["labels"].attrs[index_h5]

                if self.ch_num>1:
                    data_combined[int(ch)::2] = data 
                elif self.ch_num==1: 
                    data_combined = data

            print(len(data_combined))

            self.AWG.transfer_sequence_replay_samples(memory_index,data_combined)

        ## SET UP THE SEQUENCE STEPS    
        seq_index=index 
        print(f'seq_index {seq_index}')
        if index!=last_index:
            self.AWG.seq_set_sequence_step(seq_index,memory_index,seq_index+1,n_loop,'always',last_step=False) #TODO: include loop_count=1000 in the labscrip command generate_multiple_tones/ontrigger
            if debugging_mode:
                print('more steps:...')
        else:
            self.AWG.seq_set_sequence_step(seq_index,memory_index,seq_index,n_loop,'always',last_step=True) 
            if debugging_mode:
                
                print('...last step! Sequence ended.')
    if len(group['0'].attrs)>0:
        # self.AWG.card_write_setup() # TODO: Do we have to call that every shot or just once after the initialization?
        self.AWG.card_start()
        self.AWG.card_enable_trigger()

def check_geometry_path(self, h5_file):
    """ Check if the geometry path in the HDF5 file has changed.
    If it has changed, update the geometry path and create all paths.
    """
