#Modified by Andre FloRydberg
import labscript_utils.h5_lock
import h5py
from blacs.tab_base_classes import Worker
from . import SpectrumCard
import numpy as np

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
        self.AWG.set_sample_rate(int(self.sample_rate))

        self.channels = []
        for ch in range(2):  #changed by Andre
            if hasattr(self,f"channel_amplitude_{ch}"):
                self.channels.append(str(ch))
                # print(self.channels)
                
        if '0' in self.channels and '1' in self.channels:
            channel_status=3
        elif '0' in self.channels:
            channel_status=1
        elif '1' in self.channels:
            channel_status=2
        # print(channel_status)
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
        self.AWG.card_write_setup()

        print("\n### INITIALIZATION DONE ###\n")

        # Initialize memory for smart programming: keys=hash of instructions, Values=position in memory
        self.smart_cache = {}
        memory_size= 2**22
        bytesPerSample = self.AWG.getBytesPerSample()
        self.num_manual_samples=memory_size*bytesPerSample
        # self.num_manual_samples=4096*4
    
    def program_manual(self, values):
        self.AWG.set_generation_mode(mode='single') #added by Andre  

        if self.ch_num==1:
            if values is None:
                self.AWG.card_stop()
                return{}
            elif type(values) is float:
                # Stream single frequency
                data = SpectrumCard.generate_single_tone(values*1e6,self.num_manual_samples,self.sample_rate) # TODO: Set num_samples dynamically
                self.AWG.transfer_sequence_replay_samples(len(self.smart_cache),data) # Write in next free memory
                self.AWG.seq_set_sequence_step(0,0,0,1,'on_trigger',last_step=False)
            elif type(values) is int:
                if values == -1:
                    return {} # not memory index selected
                self.AWG.seq_set_sequence_step(0,values,0,1,'on_trigger',last_step=False) # Stream sample from memory
            else: 
                return{}
        elif self.ch_num==2:
            if values is None:
                self.AWG.card_stop()
                return{}
            elif type(values) is float:
                data = SpectrumCard.generate_single_tone(values*1e6,self.num_manual_samples,self.sample_rate) 
                data_combined=np.zeros(self.num_manual_samples*2, dtype=np.int16)
                data_combined[0::2]=data
                data_combined[1::2]=data 
                self.AWG.transfer_sequence_replay_samples(0,data_combined) 
                self.AWG.seq_set_sequence_step(0,0,0,1,'on_trigger',last_step=False) # Stream single frequency
            elif type(values) is int:
                if values == -1: 
                    return {} # not memory index selected
                self.AWG.seq_set_sequence_step(0,values,0,1,'on_trigger',last_step=False) # Stream sample from memory
            else: 
                return{}
        self.AWG.card_write_setup()
        self.AWG.card_start()
        self.AWG.card_force_trigger() # Start replay without a hardware trigger
        return {}

    def transition_to_buffered(self, device_name, h5_file, initial_values, fresh):
        self.AWG.card_stop() # If card was still running, e.g. from manual mode
        self.AWG.set_generation_mode(self.generation_mode) #added by Andre 

        with h5py.File(h5_file,'r') as f:
            group = f[f"devices/{device_name}"]
            shot_seq_length=len(group['0'].attrs)
            last_index = shot_seq_length-1

            if fresh or len(self.smart_cache)+shot_seq_length > self.memory_segments: #default value
                self.smart_cache = {} # Reset smart programming and start writing memory from the beginning otherwise monsters will arise
            void_data=np.zeros(self.num_manual_samples, dtype=np.int16)
            


            for index in range(shot_seq_length): #index of sequences
                print('Starting the configuration of sequence step '+str(index))
                index_h5 = str(index) # The index in the h5 file is a str
                instructions={}
                size=np.zeros(self.ch_num)
                for ch in self.channels:
                    ### LOOP TROUGH STREAMING STEPS ###
                    instructions[ch] = group[ch].attrs[index_h5]
                    size[int(ch)]=instructions[ch][0]
                num_samples = int(max(size))

                print(f"duration= {num_samples/self.sample_rate:.6f} s")

                data_combined= np.zeros(num_samples*self.ch_num, dtype=np.int16)
                immutable_instructions = {key: tuple(value) for key, value in instructions.items()}
                instruction_hash = hash(frozenset(immutable_instructions.items())) # Generate the hash

                if instruction_hash in self.smart_cache:
                    memory_index = self.smart_cache[instruction_hash]
                    print(f'memory_index {memory_index}')
                    print('already in memory')

                else:
                    memory_index = len(self.smart_cache)
                    print(f'memory_index {memory_index}')
                    print('new in memory')
                    self.smart_cache[instruction_hash] = memory_index
                    initial_values[memory_index] = ''
                    for ch in self.channels:
                        print('channel '+str(ch))
                        
                        ### CALCULATE DATA ###
                        if len(instructions[ch]) == 2:  # SINGLE TONE
                            data = SpectrumCard.generate_single_tone(instructions[ch][1],num_samples,self.sample_rate)
                            if index_h5 in group[ch]["labels"].attrs:
                                initial_values[memory_index] += group[ch]["labels"].attrs[index_h5]
                            else:
                                initial_values[memory_index] += f"{instructions[ch][1]*1e-6:.3f} MHz"
                        elif (len(instructions[ch])-1) % 3 == 0:  # MULTI TONE
                            num_tones = (len(instructions[ch])-1)//3
                            freq = instructions[ch][1:num_tones+1]
                            ampl = instructions[ch][num_tones+1:2*num_tones+1]
                            phase= instructions[ch][2*num_tones+1:]
                            data = SpectrumCard.generate_multi_tone(freq,ampl,phase,num_samples,self.sample_rate)
                            if index_h5 in group[ch]["labels"].attrs:
                                initial_values[memory_index] += f"f:{freq*1e-6} MHz, a:{ampl}, p:{phase}"
                            else:
                                initial_values[memory_index] += f"{instructions[ch][1]*1e-6:.3f} MHz"
                        else:
                            raise RuntimeError("Instruction length does not match, what happened??")
                        if index_h5 in group[ch]["labels"].attrs:
                            initial_values[memory_index] = group[ch]["labels"].attrs[index_h5]
                        if self.ch_num>1:
                            data_combined[int(ch)::2] = data 
                        elif self.ch_num==1: 
                            data_combined = data
                    self.AWG.transfer_sequence_replay_samples(memory_index,data_combined)
                ## SET UP THE SEQUENCE STEPS    
                seq_index=index 
                print(f'seq_index {seq_index}')
                if index!=last_index:
                    self.AWG.seq_set_sequence_step(seq_index,memory_index,seq_index+1,1,'always',last_step=False)
                    print('more steps:...')
                else:
                    self.AWG.seq_set_sequence_step(seq_index,memory_index,seq_index,1,'always',last_step=True) 
                    print('...last step! Sequence ended.')
            if len(group['0'].attrs)>0:
                self.AWG.card_write_setup() # TODO: Do we have to call that every shot or just once after the initialization?
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
        self.AWG.card_reset()
        self.init()