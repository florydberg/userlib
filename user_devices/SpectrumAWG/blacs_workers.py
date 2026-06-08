# Modified by Andre FloRydberg on 10/03/2026

import labscript_utils.h5_lock
import h5py
from blacs.tab_base_classes import Worker
from . import SpectrumCard
import numpy as np
from datetime import datetime
import threading
from .spectrum_card_waveform_generation_tool import SpectrumCardWaveformTool
import time

debugging_mode=True
reordering_mode = 0

naked_eye = 1

cores_0=[0,1,2,3,4,5,6,7,12,13,14,15,16,17,18,19]
cores_1=[8,9,10,11,20]
if naked_eye:
    n_loop=1e10#1e3#
    n_loop=int(n_loop)
else:
    n_loop=1

current_time = datetime.now()

CF = { #correction factor protecting AODs for overpower
    1: 0.5,
    2: 0.7,
    3: 0.84,
    4: 0.9,
    5: 1.0
}

def generate_multi_tone(freqs, amps, num_samples, sample_rate, phases=None):
    """
    Generate a multitone waveform with optional phase control.
    freqs: list of frequencies [Hz]
    amps: list of amplitudes
    phases: list of phases [rad] (same length as freqs). If None, all phases = 0
    """
    t = np.arange(num_samples) / sample_rate
    signal = np.zeros(num_samples)
    
    if isinstance(amps, (int, float)):
        amps = [amps] * len(freqs)
    
    if phases is None:
        phases = [0] * len(freqs)
    
    for f, a, p in zip(freqs, amps, phases):
        signal += a * np.sin(2 * np.pi * f * t + p)
    
    max_val = np.max(np.abs(signal))
    if max_val > 0:
        signal = signal / max_val
    return (signal * 32767).astype(np.int16)

class SpectrumAWGWorker(Worker):

    def init(self):

        print("### INITIALIZING IT ###\n")
        self.AWG = SpectrumCard.SpectrumCard(self.device_path,timeout=self.timeout)
        # print(self.__dir__())
        self.gemetry_path = None

        self.AWG.open()

        if self.external_clock_rate is None:
            self.AWG.set_clock('internal')
        else:
            self.AWG.set_clock('external',int(self.external_clock_rate))
        self.AWG.set_sample_rate(int(1e9))

        self.channels = []
        for ch in range(2):  #changed by Andre
            if hasattr(self,f"channel_amplitude_{ch}"):
                self.channels.append(str(ch))
                if debugging_mode:
                    print(self.channels)
                
        if '0' in self.channels and '1' in self.channels:
            channel_status=3
        elif '0' in self.channels:
            channel_status=1
        elif '1' in self.channels:
            channel_status=2
        if debugging_mode:
            print(channel_status)
        self.AWG.set_channel_status(self.channels, channel_status)

        for ch in self.channels:
                self.AWG.set_channel_enable(int(ch),True)
                self.AWG.set_channel_amplitude(int(ch),getattr(self,f"channel_amplitude_{ch}"))
                self.AWG.set_channel_filter(int(ch),False)
                self.AWG.set_channel_mode(int(ch),None)
        self.ch_num=len(self.channels)


        self.AWG.set_ext_trigger_mode('ext0','pos',rearm=True)
        self.AWG.set_ext_trigger_level('ext0',2000,800) # 2V trigger, 0.8V rearm
        self.AWG.set_trigger_or_mask(['ext0'])
        self.AWG.trigger = ['ext0']
        self.AWG.seq_set_memory_segments(self.memory_segments)
        self.AWG.change_Multi_IO('X0', 'RUNSTATE')
        self.AWG.card_write_setup()

        print("\n### INITIALIZATION DONE ###\n")

        # Initialize memory for smart programming: keys=hash of instructions, Values=position in memory
        self.smart_cache = {}
        self.smart_cache[hash('manual')] = 0 # reserve first memory segment for manual programming
        if debugging_mode:
            print(f"Memory segments available for programming: {self.memory_segments-1} (excluding manual programming segment)")

        memory_size= 2**14
        bytesPerSample = self.AWG.getBytesPerSample()
        self.num_manual_samples=memory_size*bytesPerSample
        # self.num_manual_samples=4096*4
        self.manual_sample_rate=1e9
        self.manual_trigger='software'

    def change_Multi_IO(self, connection, value):
        """
        Change the Multi IO connection to the specified value.
        """
        if debugging_mode:
            print(f'changing Multi IO {connection} to : {value}')
        self.AWG.change_Multi_IO(connection, value)
        return {}

    def change_triggerSource(self, value):
        if debugging_mode:
            print(f'changing trigger source to : {value}')
        # print('NOT IMPLEMENTED YET')
        self.AWG.set_trigger_or_mask([value])
        self.AWG.trigger = [value]
        return {}

    def change_sampleNum(self, value):
        if debugging_mode:
            print(f'changing sample number to : {2*value}') #2 because of 2 channels
        self.num_manual_samples=value*self.AWG.getBytesPerSample()
        return {}
    
    def change_sampleRate(self, value):
        if debugging_mode:
            print(f'changing sample rate to : {value} MHz')
        self.manual_sample_rate=value*1e6
        
        return {}

    def program_manual(self, values=None, amps=100):
        # self.AWG.card_stop()
        self.AWG.set_generation_mode(mode='single')  
        if debugging_mode:
            # print(type(values))
            print('samplerate', self.manual_sample_rate*1e-6)

        if isinstance(values, list):
            if debugging_mode:
                print('checking sample rate for multi-tone generation...')
            if self.manual_sample_rate <= max(values[0])*1e6*5: #and self.manual_sample_rate>values[1]*10 
                print("####  Sample rate too low for good sampling at such frequencies: increase sample rate or reduce frequencies #####")
            else:
                self.AWG.set_sample_rate(int(self.manual_sample_rate))
            
        if self.ch_num==1:
            print("BE CAREFUL: THIS FUNCTION IS DEPRECAED")
            if values is None:
                self.AWG.card_stop()
                return{}
            elif type(values) is float:
                # Stream single frequency
                if debugging_mode:
                    print('one-channel single tone generation')
                data = SpectrumCard.generate_single_tone(values*1e6,self.num_manual_samples,self.manual_sample_rate) 
                self.AWG.transfer_sequence_replay_samples(len(self.smart_cache),data, ch_number=1) # Write in next free memory
                self.AWG.seq_set_sequence_step(0,0,0,10000,'always',last_step=False)
            elif type(values) is int:
                if values == -1:
                    return {} # not memory index selected
                self.AWG.seq_set_sequence_step(0,values,0,1,'on_trigger',last_step=True) # Stream sample from memory
            else: 
                return{}
            
        elif self.ch_num == 2:
            if values is None:
                self.AWG.card_stop()
                return {}

            elif isinstance(values, list) and all(isinstance(ch, list) for ch in values):
                freqs_ch0 = [f * 1e6 for f in values[0]]
                freqs_ch1 = [f * 1e6 for f in values[1]]

                if debugging_mode:
                    print("CH0 freqs:", freqs_ch0)
                    print("CH1 freqs:", freqs_ch1)

                if False:
                    rng = np.random.default_rng(seed=13438354524)
                    phase_array_horizontal = rng.uniform(size=len(freqs_ch0))*2*np.pi*0
                    phase_array_vertical = rng.uniform(size=len(freqs_ch1))*2*np.pi*0
                
                    data0 = generate_multi_tone(freqs_ch0, amps[0], self.num_manual_samples, self.manual_sample_rate, phase_array_horizontal)
                    data1 = generate_multi_tone( freqs_ch1, amps[1], self.num_manual_samples, self.manual_sample_rate, phase_array_vertical)
                else:
                    rng = np.random.default_rng(seed=13438354524)
                    phase_array_horizontal = rng.uniform(size=len(freqs_ch0))*2*np.pi*0
                    phase_array_vertical = rng.uniform(size=len(freqs_ch1))*2*np.pi*0
                    amp_array_horizontal = np.full(len(freqs_ch0), amps[0])
                    amp_array_vertical = np.full(len(freqs_ch1), amps[1])

                    waveform_generator = SpectrumCardWaveformTool(freq_array_horizontal=np.array(freqs_ch0),
                                     freq_array_vertical=np.array(freqs_ch1),
                                     amplitude_array_horizontal= amp_array_horizontal,
                                     amplitude_array_vertical= amp_array_vertical,
                                     phase_array_horizontal=phase_array_horizontal,
                                     phase_array_vertical=phase_array_vertical,
                                     num_samples=self.num_manual_samples,
                                     sample_rate=self.manual_sample_rate/1e6  #in MHz
                                     )

                    data0 = waveform_generator.getWaveformHorizontal()
                    data1 = waveform_generator.getWaveformVertical()

                if debugging_mode:
                    def print_fft_peaks(data, sample_rate, label, n_peaks=3):
                        # Convert sample_rate to Hz if you store it in MHz
                        sr = self.manual_sample_rate

                        fft = np.fft.rfft(data)
                        freqs = np.fft.rfftfreq(len(data), d=1/sr)
                        magnitude = np.abs(fft)/32767/1000

                        # Find the largest peaks
                        idx = np.argsort(magnitude)[-n_peaks:][::-1]

                        print(f"\n{label} FFT peaks:")
                        for i in idx:
                            print(f"{freqs[i]/1e6:.3f} MHz  |  amplitude {magnitude[i]:.1f} dBm")

                    print_fft_peaks(data0, self.manual_sample_rate, "CH0")
                    print_fft_peaks(data1, self.manual_sample_rate, "CH1")

                # Interleave
                data_combined = np.zeros(self.num_manual_samples * 2, dtype=np.int16)
                data_combined[0::2] = data0
                data_combined[1::2] = data1

                self.AWG.transfer_sequence_replay_samples(0, data_combined) #0 is the position in memory reserved for manual programming

                self.AWG.seq_set_sequence_step(0, 0, 0, n_loop, 'always', last_step=True)

            elif isinstance(values, int):
                if values == -1:
                    return {}
                self.AWG.seq_set_sequence_step(0, values, 0, 1, 'always', last_step=True)
            else:
                if debugging_mode:
                    print('nothing done')
                return {}
        self.AWG.card_write_setup()
        self.AWG.card_start()
        self.AWG.card_enable_trigger()
        # self.AWG.card_force_trigger() # Start replay without a hardware trigger

        return {}

    def dds_static(self, values=None, amps=100):
        
        if values is None:
            self.AWG.card_stop()
            print("Manual DDS mode ended.")
            return {}
        else:
            print("Manual DDS mode on")
            self.AWG.set_generation_mode(mode='dds')  
            self.AWG.card_stop()
            self.AWG.set_trigger_or_mask(enable_sources=self.AWG.trigger)

            self.AWG.dds_setup(0)

            self.AWG.card_start()
            self.AWG.card_enable_trigger()

        if self.ch_num==1:
            print("BE CAREFUL: THIS FUNCTION IS DEPRECATED")

        elif self.ch_num == 2:
            if isinstance(values, list) and all(isinstance(ch, list) for ch in values):
                for k, frq in enumerate(values[0]):
                    core=cores_0[k]
                    N = len(values[0])

                    phase_opt = 2*(1+np.random.uniform(0,1)) * np.pi * k / N 
                    phase_opt = np.pi * k * (k+1)/ N  #Kitayoshi's pahse (see Omar's Thesis)


                    self.AWG.dds_static(core, frequency=frq+np.random.uniform(0,1)/10, amplitude=amps[0]*CF[N]/N, phase=phase_opt)
                print(f"DDS manual mode started for channel 0.")

                for k, frq in enumerate(values[1]):
                    core=cores_1[k]
                    N = len(values[1])

                    phase_opt = 2*(1+np.random.uniform(0,1)) * np.pi * k / N 
                    phase_opt = np.pi * k * (k+1)/ N  #Kitayoshi's pahse (see Omar's Thesis) 


                    self.AWG.dds_static(core, frequency=frq+np.random.uniform(0,1), amplitude=amps[1]*CF[N]/N, phase=phase_opt)
                print(f"DDS manual mode started for channel 1.")

                self.AWG.trigger_dds(trigger_time=10)
                self.AWG.dds_setup(1)
                print('running...')
            else:
                if debugging_mode:
                    print('nothing to do')
                return {}      

        # self.AWG.card_force_trigger() # Start replay without a hardware trigger

        return {}

    def dds_slope(self, values_i=None, values_f=None, amps=100, duration=1, c_loop=False, keep_final=False):
        if values_i is None:
            self.AWG.card_stop()
            print("Manual DDS slope mode ended.")
            return {}
        else:
            print("Manual DDS slope mode on")
            self.AWG.set_generation_mode(mode='dds')  
            self.AWG.card_stop()

            self.AWG.dds_setup(0, trigger_time=duration)
            self.AWG.card_start()
            self.AWG.card_enable_trigger()

        if self.ch_num == 2:
            if isinstance(values_i, list) and all(isinstance(ch, list) for ch in values_i):

                for frq in range(len(values_i[0])):
                    core=cores_0[frq]
                    N = len(values_i[0])
                    self.AWG.dds_static(core, frequency=values_i[0][frq], amplitude=amps[1]*CF[N]/N)
                print(f"DDS manual static mode started for channel 0.")
                for frq in range(len(values_i[1])):
                    core=cores_1[frq]
                    N = len(values_i[1])
                    self.AWG.dds_static(core, frequency=values_i[1][frq], amplitude=amps[1]*CF[N]/N)
                print(f"DDS manual static mode started for channel 1.")

                self.AWG.trigger_dds(trigger_time=0)

                for frq in range(len(values_f[0])):
                    core=cores_0[frq]
                    N = len(values_f[0])
                    self.AWG.dds_slope(core, frequency_per_sec=(values_f[0][frq]-values_i[0][frq])/duration*1e3, amplitude=amps[0]*CF[N]/N)
                print(f"DDS manual slope mode started for channel 0.")
                for frq in range(len(values_f[1])):
                    core=cores_1[frq]
                    N = len(values_f[1])
                    self.AWG.dds_slope(core, frequency_per_sec=(values_f[1][frq]-values_i[1][frq])/duration, amplitude=amps[1]*CF[N]/N)
                print(f"DDS manual slope mode started for channel 1.")

                self.AWG.trigger_dds(trigger_time=1)

                if keep_final:
                    for frq in range(len(values_f[0])):
                        core=cores_0[frq]
                        N = len(values_f[0])
                        self.AWG.dds_static(core, frequency=values_f[0][frq], amplitude=amps[1]*CF[N]/N)
                    print(f"DDS manual static mode started for channel 0.")
                    for frq in range(len(values_f[1])):
                        core=cores_1[frq]
                        N = len(values_f[1])
                        self.AWG.dds_static(core, frequency=values_f[1][frq], amplitude=amps[1]*CF[N]/N)
                    print(f"DDS manual static mode started for channel 1.")

                    self.AWG.trigger_dds(trigger_time=duration)

                self.AWG.dds_setup(1)
                print('should be working...')
            else:
                if debugging_mode:
                    print('nothing to do')
                return {}      

        time.sleep(1)
        self.AWG.card_force_trigger() # Start replay without a hardware trigger

        time.sleep(1)
        self.AWG.card_force_trigger() # Start replay without a hardware trigger

        time.sleep(duration/1e3)
        self.AWG.card_force_trigger() # Start replay without a hardware trigger

        time.sleep(duration/1e3)
        self.AWG.card_force_trigger() # Start replay without a hardware trigger        
        time.sleep(1)
        self.dds_slope(None)
        if c_loop:
            self.AWG.card_stop()
            self.dds_slope(values_i=values_i, values_f=values_f, amps=amps, duration=duration, c_loop=c_loop, keep_final=keep_final)

        return {}

    def sequence_thread(self, device_name, h5_file, fresh):
        with h5py.File(h5_file,'r') as f:
            print("waiting for reordering instructions")
            while True:
                try:
                    group = f[f"devices/{device_name}"]
                    seq_group = f[f"reordering_sequence"]
                    shot_seq_length = len(seq_group['move'].attrs)
                    move_labels = group[ch].attrs['labels']

                    if fresh or len(self.smart_cache)+shot_seq_length > self.memory_segments: #default value
                        self.smart_cache = {} # Reset smart programming and start writing memory from the beginning otherwise monsters will arise
                        self.smart_cache[hash('manual')] = 0 # reserve first memory segment for manual programming

                    for index in range(shot_seq_length): #index of sequences
                        if debugging_mode:
                            print('Starting the configuration of sequence step '+str(index))

                        index_h5 = str(index) # The index in the h5 file is a str
                        last_index = shot_seq_length-1

                        ## discovering nummer of samples:
                        instructions={}
                        size=np.zeros(self.ch_num)
                        for ch in self.channels:
                            instructions[ch] = group[ch].attrs[index_h5]
                            size[int(ch)]=instructions[ch]
                        num_samples = int(max(size))
                        ###################################

                        if debugging_mode:
                            print(num_samples)
                            print(self.sample_rate)
                            print(f"duration = {num_samples/self.sample_rate:.6f} s")

                        ## SET UP THE SEQUENCE STEPS                         
                        data_combined= np.zeros(num_samples*self.ch_num, dtype=np.int16)

                        instruction_label=seq_group['move'].attrs[index_h5] 
                        print(f'seq_step {index_h5} : {instruction_label}') 

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

                            for ch in self.channels:
                                if debugging_mode:
                                    print('channel '+str(ch))
                                move_index = np.where(move_labels == instruction_label)[0][0]
                                if move_index.size > 0:
                                    data = group[ch]["sample"].attrs[move_index]
                                else:
                                    print(f"No data found for label {instruction_label} in channel {ch}.")

                                if self.ch_num>1:
                                    data_combined[int(ch)::2] = data 
                                elif self.ch_num==1: 
                                    data_combined = data

                            self.AWG.transfer_sequence_replay_samples(memory_index,data_combined)

                        seq_index=index_h5
                        
                        print(f'seq_index {seq_index}')
                        if index!=last_index:
                            self.AWG.seq_set_sequence_step(seq_index,memory_index,seq_index+1,n_loop,'always',last_step=False)
                            if debugging_mode:
                                print('more steps:...')
                        else:
                            self.AWG.seq_set_sequence_step(seq_index,memory_index,seq_index,n_loop,'always',last_step=True) 
                            if debugging_mode: 
                                print('...last step! Sequence ended.')

                    if len(group['0'].attrs)>0:
                        self.AWG.card_start()
                        self.AWG.card_enable_trigger() #TODO: force trigger
                        self.AWG.card_force_trigger()

                except KeyError:
                    # print("no reordering instructions found, waiting for updates...")
                    continue

    def transition_to_buffered(self, device_name, h5_file, initial_values, fresh):
        if False:
            self.AWG.card_stop() # If card was still running, e.g. from manual mode
            self.AWG.set_generation_mode(self.generation_mode)
            self.AWG.set_sample_rate(int(self.sample_rate))
            # self.AWG.set_trigger_or_mask([self.trigger_connection]) # TODO: make it read from connection table self.trigger_connection

            if not reordering_mode:
                with h5py.File(h5_file,'r') as f:

                    group = f[f"devices/{device_name}"]
                    shot_seq_length=len(group['0'].attrs)
                    last_index = shot_seq_length-1

                    if fresh or len(self.smart_cache)+shot_seq_length > self.memory_segments: #default value
                        self.smart_cache = {} # Reset smart programming and start writing memory from the beginning otherwise monsters will arise
                        self.smart_cache[hash('manual')] = 0 # reserve first memory segment for manual programming


                    for index in range(shot_seq_length): #index of sequences
                        if debugging_mode:
                            print('Starting the configuration of sequence step '+str(index))
                        index_h5 = str(index) # The index in the h5 file is a str
                        instructions={}
                        size=np.zeros(self.ch_num)
                        for ch in self.channels:
                            ### LOOP TROUGH STREAMING STEPS ###
                            instructions[ch] = group[ch].attrs[index_h5]

                            size[int(ch)]=instructions[ch]
                        num_samples = int(max(size))
                        

                        if debugging_mode:
                            print(num_samples)
                            print(self.sample_rate)
                            print(f"duration = {num_samples/self.sample_rate:.6f} s")

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
                        
                                if index_h5 in group[ch]["labels"].attrs:
                                    initial_values[memory_index] = group[ch]["labels"].attrs[index_h5]

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
                        # self.AWG.card_force_trigger() #TODO: force trigger

            else:
                with h5py.File(h5_file,'r') as f:
                    new_geometry_path = f[f"globals/Calibration AWG"].attrs['geometry_path']
                    if new_geometry_path != self.gemetry_path:
                        self.gemetry_path = new_geometry_path
                        print(f"New geometry path detected: {self.gemetry_path}")
                        fresh=True
                    
                print("Starting reordering sequence thread")
                self.reordering_thread = threading.Thread(
                    target=self.sequence_thread,
                    args=(device_name, h5_file, fresh),
                    daemon=True,
                )
                self.reordering_thread.start()

        return initial_values

    def transition_to_manual(self):
        if False:
            self.AWG.card_stop()
        return True

    def shutdown(self):
        self.AWG.card_stop()
        self.AWG.card_close()

    def abort_buffered(self):
        return self.transition_to_manual()

    def abort_transition_to_buffered(self):
        return True

    def card_reset(self):
        self.AWG.card_stop()
        self.AWG.card_reset()
        self.init()