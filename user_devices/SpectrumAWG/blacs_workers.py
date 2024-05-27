import labscript_utils.h5_lock
import h5py
from blacs.tab_base_classes import Worker
from . import SpectrumCard
import numpy as np

class SpectrumAWGWorker(Worker):
    def init(self):
        print("### INITIALIZE ###\n")
        self.AWG = SpectrumCard.SpectrumCard(self.device_path,timeout=self.timeout)
        self.AWG.open()
        if self.external_clock_rate is None:
            self.AWG.set_clock('internal')
        else:
            self.AWG.set_clock('external',int(self.external_clock_rate))
        self.AWG.set_sample_rate(int(self.sample_rate))

        self.channels = []
        for ch in range(2):
            if hasattr(self,f"channel_amplitude_{ch}"):
                self.channels.append(str(ch))
                self.AWG.set_channel_status(ch,True)
                self.AWG.set_channel_enable(ch,True)
                self.AWG.set_channel_amplitude(ch,getattr(self,f"channel_amplitude_{ch}"))
                self.AWG.set_channel_filter(ch,False)
                self.AWG.set_channel_mode(ch,None)

        self.AWG.set_ext_trigger_mode('ext0','pos',rearm=True)
        self.AWG.set_ext_trigger_level('ext0',2000,800) # 2V trigger, 0.8V rearm
        self.AWG.set_trigger_or_mask(['ext0'])
        self.AWG.set_generation_mode(mode='single')
        self.AWG.seq_set_memory_segments(self.memory_segments)

        print("\n### INITIALIZATION DONE ###\n")

        # Initialize memory for smart programming
        # Keys: hash of instructions, Values: position in memory
        self.smart_cache = {}
    
    def program_manual(self, values):
        if values is None:
            self.AWG.card_stop()
            return{}
        elif type(values) is float:
            # Stream single frequency
            data = SpectrumCard.generate_single_tone(values*1e6,4096,self.sample_rate) # TODO: Set num_samples dynamically
            self.AWG.transfer_sequence_replay_samples(len(self.smart_cache),data) # Write in next free memory
            self.AWG.seq_set_sequence_step(0,len(self.smart_cache),0,1,'on_trigger',last_step=False)
        elif type(values) is int:
            if values == -1:
                return {} # not memory index selected
            # Stream sample from memory
            self.AWG.seq_set_sequence_step(0,values,0,1,'on_trigger',last_step=False)
        else: 
            return{}
        self.AWG.card_write_setup()
        self.AWG.card_start()
        self.AWG.card_force_trigger() # Start replay without a hardware trigger
        return {}

    def transition_to_buffered(self, device_name, h5_file, initial_values, fresh):
        self.AWG.card_stop() # If card was still running, e.g. from manual mode
        with h5py.File(h5_file,'r') as f:
            group = f[f"devices/{device_name}"]
            for ch in self.channels:
                if fresh or len(self.smart_cache)+len(group[ch].attrs) > self.memory_segments:
                    # Reset smart programming and start writing memory from the beginning
                    # TODO: What if we want to always keep specific instruction in the memory?
                    self.smart_cache = {}

                last_index = len(group[ch].attrs)-1
                for index in range(len(group[ch].attrs)):
                    index_h5 = str(index) # The index in the h5 file is a str
                    ### LOOP TROUGH STREAMING STEPS ###
                    instruction = group[ch].attrs[index_h5]
                    instruction_hash = hash(instruction.tobytes())
                    if instruction_hash in self.smart_cache:
                        memory_index = self.smart_cache[instruction_hash]
                    else:
                        memory_index = len(self.smart_cache)
                        self.smart_cache[instruction_hash] = memory_index
                        ### CALCULATE DATA ###
                        num_samples = int(instruction[0])
                        if len(instruction)==2: 
                            # SINGLE TONE
                            data = SpectrumCard.generate_single_tone(instruction[1],num_samples,self.sample_rate)
                            initial_values[memory_index] = f"{instruction[0]}Hz"
                        elif (len(instruction)-1)%3 == 0: 
                            # MULTI TONE
                            num_tones = (len(instruction)-1)//3
                            freq = instruction[1:num_tones+1]
                            ampl = instruction[num_tones+1:2*num_tones+1]
                            phase= instruction[2*num_tones+1:]
                            data = SpectrumCard.generate_multi_tone(freq,ampl,phase,num_samples,self.sample_rate)
                            initial_values[memory_index] = f"f:{freq}Hz, a:{ampl}, p:{phase}"
                        else:
                            raise RuntimeError("Instruction length does not match, what happened??")
                        
                        if index_h5 in group[ch]["labels"].attrs:
                            initial_values[memory_index] = group[ch]["labels"].attrs[index_h5]
                            
                        self.AWG.transfer_sequence_replay_samples(memory_index,data)
                    if index!=last_index:
                        self.AWG.seq_set_sequence_step(step_index=index,segment_index=memory_index,next_step=index+1,loop_count=1,end_loop_condition='on_trigger',last_step=True)
                    else:
                        self.AWG.seq_set_sequence_step(index,memory_index,index,1,'on_trigger',last_step=False)
                        # If there is a trigger at the stop time, repeat one last sequence 
                        # and then stop (if not card_stop() was called already)
                        self.AWG.seq_set_sequence_step(index+1,memory_index,0,1,'always',last_step=True)
                # ONLY IMPLEMENTED FOR ONE CHANNEL, IF TWO CHANNELS ARE NEEDED WE ALREADY GET AN ERROR IN LABSCRIPT
                # FOR IMPLEMENTATION ONE HAS TO INTERWEAVE THE DATA FOR BOTH CHANNELS
                break 

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
