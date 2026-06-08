# Modified by Andre FloRydberg on 15/05/2025

import labscript_utils.h5_lock
import h5py
from blacs.tab_base_classes import Worker
from . import SpectrumCard
import numpy as np
from datetime import datetime

debugging_mode=False
naked_eye = 0
remote_cntrl = 0
if naked_eye:
    n_loop=1e6
    n_loop=int(n_loop)
else:
    n_loop=1

current_time = datetime.now()

class SpectrumAWGWorker(Worker):

    def init(self):

        print("### INITIALIZING IT ###\n")
        self.AWG = SpectrumCard.SpectrumCard(self.device_path,timeout=self.timeout)
        # print(self.__dir__())

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
        self.AWG.seq_set_memory_segments(self.memory_segments)
        self.AWG.change_Multi_IO('X0', 'RUNSTATE')
        self.AWG.card_write_setup()

        print("\n### INITIALIZATION DONE ###\n")

        # Initialize memory for smart programming: keys=hash of instructions, Values=position in memory
        self.smart_cache = {}
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
        print('NOT IMPLEMENTED YET')
        self.AWG.set_trigger_or_mask([value])
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
        self.AWG.set_generation_mode(mode='single')  
        if debugging_mode:
            print(type(values))
            print(self.manual_sample_rate*1e-6)

        if isinstance(values, list):
            if debugging_mode:
                print('checking')
            if self.manual_sample_rate <= values[0]*1e6*10: #and self.manual_sample_rate>values[1]*10 
                print("####  Sample rate too low for good sampling at such frequencies: increase sample rate or reduce frequencies #####")
            else:
                self.AWG.set_sample_rate(int(self.manual_sample_rate))
            
        if self.ch_num==1:
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
        elif self.ch_num==2:
            if values is None:
                self.AWG.card_stop()
                return{}
            elif isinstance(values, list) and all(isinstance(x, (int, float)) for x in values): #type(values) is float or  type(values) is float:
                if debugging_mode:
                    print('two-channel single tone generation')
                data0 = SpectrumCard.generate_manual_tone(values[0]*1e6, amps[0], self.num_manual_samples,self.manual_sample_rate) 
                data1 = SpectrumCard.generate_manual_tone(values[1]*1e6, amps[1], self.num_manual_samples,self.manual_sample_rate) 
                data_combined=np.zeros(self.num_manual_samples*2, dtype=np.int16)
                data_combined[0::2]=data0
                data_combined[1::2]=data1 
                self.AWG.transfer_sequence_replay_samples(len(self.smart_cache),data_combined) 
                self.AWG.seq_set_sequence_step(0,0,0,1,'on_trigger',last_step=False) # Stream single frequency
            elif type(values) is int:
                if values == -1: 
                    return {} # not memory index selected
                self.AWG.seq_set_sequence_step(0,values,0,1,'always',last_step=True) # Stream sample from memory
            else: 
                if debugging_mode:
                    print('nothing done')
                return{}
        self.AWG.card_write_setup()
        self.AWG.card_start()
        self.AWG.card_force_trigger() # Start replay without a hardware trigger

        return {}

    def transition_to_buffered(self, device_name, h5_file, initial_values, fresh):
        self.AWG.card_stop() # If card was still running, e.g. from manual mode
        self.AWG.set_generation_mode(self.generation_mode)
        self.AWG.set_sample_rate(int(self.sample_rate))
        # self.AWG.set_trigger_or_mask([self.trigger_connection]) # TODO: make it read from connection table self.trigger_connection

        if not remote_cntrl:
            with h5py.File(h5_file,'r') as f:
                group = f[f"devices/{device_name}"]
                shot_seq_length=len(group['0'].attrs)
                last_index = shot_seq_length-1

                if fresh or len(self.smart_cache)+shot_seq_length > self.memory_segments: #default value
                    self.smart_cache = {} # Reset smart programming and start writing memory from the beginning otherwise monsters will arise

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

        else:
            with h5py.File(h5_file,'r') as f:
                group = f[f"devices/{device_name}"]
                shot_seq_length=len(group['0'].attrs)
                last_index = shot_seq_length-1

                if fresh or len(self.smart_cache)+shot_seq_length > self.memory_segments: #default value
                    self.smart_cache = {} # Reset smart programming and start writing memory from the beginning otherwise monsters will arise

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


        return initial_values

    def transition_to_manual(self):
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