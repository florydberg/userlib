import time
from user_devices.SpectrumAWG.SpectrumCard import *

# Main Code
if __name__ == "__main__":

    # Open Connection to Card
    tweezerAWG = SpectrumCard('/dev/spcm0')
    tweezerAWG.open()
    #tweezerAWG.print_available_pci_features()
    #tweezerAWG.print_sequence_setting_limits()

    # Set sampling rate, clock and output channels
    sample_rate = MEGA(1250)
    tweezerAWG.set_clock('external',MEGA(10))
    tweezerAWG.set_sample_rate(sample_rate)
    tweezerAWG.set_channel_status(0,True)
    tweezerAWG.set_channel_enable(0,True)
    tweezerAWG.set_channel_amplitude(0,100)
    tweezerAWG.set_channel_filter(0,False)
    tweezerAWG.set_channel_mode(0,'double')

    # Trigger Settings
    #tweezerAWG.print_available_trigger_sources()
    #tweezerAWG.print_available_ext_trigger_modes()
    #tweezerAWG.print_available_and_trigger_sources()
    #tweezerAWG.print_available_or_trigger_sources()
    tweezerAWG.set_ext_trigger_mode('ext0','pos',rearm=True)
    tweezerAWG.set_ext_trigger_level('ext0',800,2000)
    tweezerAWG.set_trigger_or_mask({'ext0'})

    # Set Generation Mode
    demo_mode = 'seq' # 'single', 'seq', 'fifo'
    # 'single': Configures the card for single-shot data replay, where a fixed set of data is played once after the first trigger.
    # 'seq': Sets the card to sequence mode, allowing for complex, multi-step sequences of data to be replayed in a specified order.
    # 'fifo': Configures the card for FIFO mode, enabling continuous data streaming by replenishing data in real-time.

    if demo_mode == 'single':
        tweezerAWG.set_generation_mode(mode='single')
        tweezerAWG.set_loops(0)
    elif demo_mode == 'seq':
        tweezerAWG.set_generation_mode(mode='sequence')
        tweezerAWG.seq_set_memory_segments(2**16)
    elif demo_mode == 'fifo':
        tweezerAWG.set_generation_mode(mode='fifo_single')


    # Generate Data
    if demo_mode == 'single' or demo_mode == 'fifo':
        num_samples = 4096*320 # Has to be a multiple of 4096 !!!
        fundamental_frequency = sample_rate/num_samples # Only integer multiples of this frequency can be generated

        # Generate Single Tone
        frequency = fundamental_frequency*100
        samples = generate_single_tone(frequency, num_samples)

        # Generate Multi Frequency Tones
        #unique_random_numbers = random.sample(range(100, 2000, 10), 100)
        #frequency_list = [num * fundamental_frequency for num in unique_random_numbers]
        #samples=generate_multi_tone(frequency_list,np.ones(len(frequency_list)),num_samples,sample_rate)

    # Write Data to Card
    if demo_mode == 'single':
        tweezerAWG.transfer_single_replay_samples(samples)
    if demo_mode == 'fifo':
        notify_size = 4096*32
        tweezerAWG.fifo_initialize_buffer(samples,notify_size)    
    
    # Generate and Write Sequence Data
    if demo_mode == 'seq':
        num_samples = 4096
        fundamental_frequency = sample_rate/num_samples

        for i in range(100):
            data = generate_single_tone(fundamental_frequency*(i+1),num_samples)
            tweezerAWG.transfer_sequence_replay_samples(i,data)
            if i < 99:
                tweezerAWG.seq_set_sequence_step(i,i,i+1,1,'on_trigger',last_step=False)
            else:
                tweezerAWG.seq_set_sequence_step(i,i,0,1,'on_trigger',last_step=True)


    tweezerAWG.card_write_setup()
    tweezerAWG.card_start()

    input()
    tweezerAWG.card_force_trigger()
    if demo_mode == 'single':
        input()

    if demo_mode == 'seq':
        for i in range(100):
            input()
            tweezerAWG.card_force_trigger()

    if demo_mode == 'fifo':
        fifo_bytes_avail_user = int32(0) 
        fifo_pos_pc = int32(0)

        start_time = time.time() 
        while (time.time()-start_time) < 5:
            
            # Get number of free bytes on card memory that can be written:
            spcm_dwGetParam_i32(tweezerAWG.hCard, SPC_DATA_AVAIL_USER_LEN, byref(fifo_bytes_avail_user))
            # Position of pointer in PC buffer (would be needed if data is actually updated)
            spcm_dwGetParam_i32(tweezerAWG.hCard, SPC_DATA_AVAIL_USER_POS, byref(fifo_pos_pc))

            #If enough bytes are free, write new data to FIFO
            if fifo_bytes_avail_user.value > notify_size:
                dwError = spcm_dwSetParam_i32(tweezerAWG.hCard, SPC_DATA_AVAIL_CARD_LEN, notify_size)
                if dwError != ERR_OK:
                    tweezerAWG.handle_error()
                    
            #Wait for current data transfer (of size notify_size) to be finished
            dwError = spcm_dwSetParam_i32(tweezerAWG.hCard, SPC_M2CMD, M2CMD_DATA_WAITDMA)
    
    tweezerAWG.card_stop()
    tweezerAWG.card_close()