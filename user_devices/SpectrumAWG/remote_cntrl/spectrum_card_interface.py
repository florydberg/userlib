# Author: Marcus Culemann (modified by Andrea Fantini (added by Andrea))
# Version: March 2024

from pyspcm import *
from spcm_tools import *
import sys
from dataclasses import dataclass
from functools import reduce
from operator import ior
import numpy as np
import time

######################################################################################################
## This file implements some functions provided by Spectrum Instrumentation in a more pythonic way. ##
## We only consider functions that are important for the replay of signals with M4i.6621-x8         ## or M4i.6631-x8     (added by Andrea)   
## Some functions might not be implemented yet. Fell free to add them.                              ##
######################################################################################################
@dataclass
class SpectrumCardInterface():
    """
    Class that provides an object oriented way of dealing with the Spectrum Card M4i.6621-x8.
    Class attributes:
        cardId: X in /dev/spcmX handle name. See Spectrum control center. Default 0.
        sampleRate: in MS/s. Default 625.
        ch1 and ch2: Boolean to enable each channel.
        replay_mode: choose 'single','multi','gate','singlestart','sequence','continuous','fifo_single','fifo_multi','fifo_gate'
        memory_size: Number of samples per channel. Allowed values are Min: 32 and then steps of 32.
                     (Interesting note: Each sample takes 2 bytes.)
        num_loops: Number of times the memory should be repeated. See manual for behaviour in different modes.
        amplitude_ch1: Amplitude of channel 1 into 50 Ohm load in mV. Valid setting are 80 to 2500.
        amplitude_ch2: Amplitude of channel 2 into 50 Ohm load in mV. Valid setting are 80 to 2500.
        replay_data_ch1: 1D numpy array that contains the voltages as 16 bit integers for each sample point. 
                         Maximum is given by amplitude setting. Range is then +- amplitude.
        replay_data_ch2: 1D numpy array that contains the voltages as 16 bit integers for each sample point. 
                         Maximum is given by amplitude setting. Range is then +- amplitude.
        filter_ch1: Choose False for no filter and True for 65 MHz cutoff.
        filter_ch2: Choose False for no filter and True for 65 MHz cutoff.

        Trigger configuration:
        1) Configure the analog inputs of the trigger system.
            main_trigger_termination: Choose 'high' or '50Ohm'.
            main_trigger_coupling: Choose 'AC' or 'DC'.
            main_trigger_mode: See setMainTriggerMode() for details.
            secondary_trigger_mode: See setSecondaryTriggerMode() for details.
            main_trigger_level0: Trigger level for most modes. Level in mV. Limit -10000 to 10000. Steps of 10.
            main_trigger_level1: Second trigger level for window and rearm modes. Level in mV. Limit -10000 to 10000. Steps of 10.
            secondary_trigger_level0: Trigger level for most modes. Limit -10000 to 10000. Steps of 10.
        2) The trigger is processed by so-called trigger modes. 
        The trigger modes are defined by a OR mask and an AND mask. Their outputs are again combined by an AND.
        trigger_or_tuple: Choose the trigger modes for the OR mask. Options are 'none', 'software', 'ext0', 'ext1'. 
            'software' triggers immediately after the card starts. 
            'ext0' is the main trigger, 'ext1' is secondary trigger with limited functionality.
            You can choose multiple modes at the same time. Single arguments are passed e.g. as ('software',). Don't forget the comma!
        trigger_and_tuple: Similar to OR mask. Options are 'none', 'ext0', 'ext1'.
        3) Specify a final trigger delay.
            trigger_delay_samples: Trigger delay in samples. The total delay will be trigger_delay_samples / sample_rate.
            
    Usage:
        1) Choose desired parameters either on construction of the object or calling object.parameter = ...
           You have to provide some replay_data!
        2) Upload the parameters to the card via the setupCard() function
        3) Arm the trigger by calling armTrigger(). Once the triger is armed, some settings can no longer be changed or read.
        (...)
        Close the card with the object.closeCard()
    """
    # This syntax might be a bit unconventional. It is just a short form together with the @dataclass decorator 
    # to skip a bit of code. Just read it as if it was in an __init__ function. For all the values defined here
    #  self. ... equivalents are automatically generated.
    cardId: int = 0
    sampleRate: int = 625
    ch1_enabled: bool = False
    ch2_enabled: bool = False
    replay_mode: str = 'single'
    memory_size: int = 2**16
    num_loops: int = 1
    main_trigger_termination: str = 'high'
    main_trigger_coupling: str = 'AC'
    main_trigger_mode: str = 'pos'
    secondary_trigger_mode: str = 'pos'
    main_trigger_level0: int = 2500
    main_trigger_level1: int = 5000
    secondary_trigger_level0: int = 2500
    trigger_or_tuple: tuple = ('software',)
    trigger_and_tuple: tuple = ('software',)
    trigger_delay_samples: int = 0
    amplitude_ch1: int = 158 # -6 dBm
    amplitude_ch2: int = 158 # -6 dBm
    replay_data_ch1: np.ndarray = None
    replay_data_ch2: np.ndarray = None
    filter_ch1: bool = False
    filter_ch2: bool = False
    defaultTimeout: int = 10000 #ms


    def setupCard(self):
        """
        Setup the card with the chosen configuration.
        """
        self.hCard = self.getCardHandle(self.cardId)
        # Check that card can do replay
        if not self.checkReplayPossible():
            print('The connected card does not provide a pure analog out mode.')
            sys.exit(1)
        # Set clock mode to internal
        self.setClockModeInternal()
        # Upload sample rate
        self.setSampleRate(self.sampleRate)
        # Enable selected channels
        self.enableChannels(self.ch1_enabled, self.ch2_enabled)
        # Setup replay mode
        self.setReplayMode(self.replay_mode)
        # Setup memory size
        self.setMemorySize(self.memory_size)
        # Setup number of loops
        self.setNumLoops(self.num_loops)
        
        # Setup main trigger hardware
        self.setMainTriggerInputTermination(self.main_trigger_termination)
        self.setMainTriggerInputCoupling(self.main_trigger_coupling)
        # Setup trigger modes
        self.setMainTriggerMode(self.main_trigger_mode)
        self.setSecondaryTriggerMode(self.secondary_trigger_mode)
        # Setup trigger levels
        self.setMainTriggerLevel(self.main_trigger_level0, self.main_trigger_level1)
        self.setSecondaryTriggerLevel(self.secondary_trigger_level0)
        # Setup trigger mask OR
        self.setTriggerMaskOR(self.trigger_or_tuple)
        # Setup trigger mask AND
        self.setTriggerMaskAND(self.trigger_and_tuple)
        # Setup trigger delay
        self.setTriggerDelay(self.trigger_delay_samples)
        # Setup trigger Timout
        self.setTimeout(self.defaultTimeout) #(added by Andrea)

        # Setup amplitudes of channels
        self.setupAmplitudes(self.amplitude_ch1, self.amplitude_ch2)
        # Setup output filter
        self.setupFilters(self.filter_ch1, self.filter_ch2)
        # Enable outputs
        self.enableOutputs(self.ch1_enabled, self.ch2_enabled)
        # Setup memory buffer
        self.bytesPerSample = self.getBytesPerSample()
        self.setupBuffer()
        # Upload the replay data
        self.uploadData()
        
    def getCardHandle(self, cardId):
        """
        Get the handle of the card number "cardId".
        The cardId is given in the folder of the driver (see /dev/spcmXX).
        """
        string = f'/dev/spcm{cardId}'.encode()
        hCard = spcm_hOpen(create_string_buffer(string))
        # If no card is found
        if not hCard:
            print('No card found. Did you pass the right cardId? Check if there are other hosts...')
            sys.exit(1) # Exit code for "An error occured."
        return hCard
    
    def closeCard(self):
        """
        Execute final actions to properly close the card.
        """
        self.disarmTrigger()
        spcm_vClose(self.hCard)
        print('Card Closed')

    def getCardType(self):
        """
        Get the card type encoded as int32. See getCardName for human readable return.
        """
        lCardType = int32(0)
        spcm_dwGetParam_i32(self.hCard, SPC_PCITYP, byref(lCardType))
        return lCardType
    
    def getCardName(self):
        """
        Get the name of the card in human readable form.
        """
        lCardType = self.getCardType()
        name = szTypeToName(lCardType.value)
        return name
    
    def getSerialNumber(self):
        """
        Get the card serial number as int32.
        """
        lSerialNumber = int32(0)
        spcm_dwGetParam_i32(self.hCard, SPC_PCISERIALNO, byref(lSerialNumber))
        return lSerialNumber
    
    def getFunctionType(self):
        """
        Get the function type of the card, i.e. digital I/O, analog out, ...
        Encoded as int32. See manual p. 69 for the meaning of the values.
        For the M4i.6621-x8 the function type is 2, i.e. analog out. 
        """
        lFncType = int32(0)
        spcm_dwGetParam_i32(self.hCard, SPC_FNCTYPE, byref(lFncType))
        return lFncType
    
    def checkReplayPossible(self):
        """
        Check, whether the card connected is able to replay signals in the analog out mode.
        Returns True if this is the case, else False.
        """
        lFncType = self.getFunctionType()
        lFncTypeVal = lFncType.value

        if not lFncTypeVal == SPCM_TYPE_AO:
            print("The connected card is not exclusively an arbitrary waveform generator. This code is only made for analog out mode.")
            return False
        else:
            return True

    def setSampleRate(self, sampleRate):
        """
        Set the sample rate in MHz of the card. Only pick integer MHz. 
        """
        spcm_dwSetParam_i64(self.hCard, SPC_SAMPLERATE, MEGA(sampleRate))
        actualSampleRate = int64(0)
        spcm_dwGetParam_i64(self.hCard, SPC_SAMPLERATE, byref(actualSampleRate))

        if not actualSampleRate:
            print('Invalid sampling rate. Check device limits.')
            sys.exit(1)

        if not actualSampleRate.value/1e6 == sampleRate:
            print(f'Could not match the desired sampling rate. The actual sample rate is {actualSampleRate.value*1e-6} MHz.')

    def setClockModeInternal(self):
        """
        Our default use case only requires the internal clock. 
        """
        spcm_dwSetParam_i32(self.hCard, SPC_CLOCKMODE, SPC_CM_INTPLL)
       
    def enableChannels(self, ch1: bool, ch2: bool):
        """
        Enable different channels by passing True or False to the respective argument.
        """
        # Create bitmap
        bitmap = ch1*1 | ch2*2
        bitmap = uint32(bitmap)
        # Set on device
        spcm_dwSetParam_i32(self.hCard, SPC_CHENABLE, bitmap)

        # Confirm that this worked
        actualEnabledChannels = int32(0)
        spcm_dwGetParam_i32(self.hCard, SPC_CHENABLE, byref(actualEnabledChannels))

        if not actualEnabledChannels:
            print('Could not enable selected channels. Is any channel enabled?')
            sys.exit(1)

    def getNumAvtivatedChannels(self):
        """
        Return the number of activated channels.
        """
        actualEnabledChannels = int32(0)
        spcm_dwGetParam_i32(self.hCard, SPC_CHCOUNT, byref(actualEnabledChannels))
        return actualEnabledChannels.value
    
    def enableOutputs(self, ch1_enable: bool, ch2_enable: bool):
        """
        Enable the output of the selected channels. Choose True to enable and False to disable.
        Outputs will be (dis-)connected via relay. A disconnected channel does not have a defined level.
        """
        if ch1_enable:
            spcm_dwSetParam_i32(self.hCard, SPC_ENABLEOUT0, int32(1))
        if ch2_enable:
            spcm_dwSetParam_i32(self.hCard, SPC_ENABLEOUT1, int32(1))

    def getAvailableReplayModes(self):
        """
        Return the available replay modes as bitsring. For M4i.6621-x8 the available modes
        are lsited in the doctrsing of the class.
        """
        bitstring = int32(0)
        spcm_dwGetParam_i32(self.hCard, SPC_AVAILCARDMODES, byref(bitstring))
        return bitstring.value      

    def setReplayMode(self, mode_str: str):
        """
        Options are
        'single','multi','gate','singlestart','sequence','continuous','fifo_single','fifo_multi','fifo_gate'
        """
        mode_dict = {'single': SPC_REP_STD_SINGLE,\
                     'multi': SPC_REP_STD_MULTI,\
                     'gate': SPC_REP_STD_GATE,\
                     'singlestart': SPC_REP_STD_SINGLERESTART,\
                     'sequence': SPC_REP_STD_SEQUENCE,\
                     'fifo_single': SPC_REP_FIFO_SINGLE,\
                     'fifo_multi': SPC_REP_FIFO_MULTI,\
                     'continuous': SPC_REP_STD_CONTINUOUS}
        
        mode = mode_dict[mode_str]
        spcm_dwSetParam_i32(self.hCard, SPC_CARDMODE, mode)

    def setMemorySize(self, samples_per_channel):
        """
        Set the memory size in samples per channel. 
        """
        spcm_dwSetParam_i64(self.hCard, SPC_MEMSIZE, int64(samples_per_channel))

    def getBytesPerSample(self):
        """
        Return the bytes per sample. Default should be 2 bytes. 
        """
        bytesPerSample = int32(0)
        spcm_dwGetParam_i32(self.hCard, SPC_MIINST_BYTESPERSAMPLE, byref(bytesPerSample))
        return bytesPerSample.value

    def setNumLoops(self, numLoops):
        """
        Set the number of times the memory should be replayed. 0 corresponds to continuous replay for most modes.
        Check the manual for details.
        """
        spcm_dwSetParam_i64(self.hCard, SPC_LOOPS, int64(numLoops))

    def setMainTriggerInputTermination(self, termination):
        """
        Select the input termination of the main trigger Trg0/Ext0. 
        Options are 'high' and '50Ohm'. High corresponds to 1kOhm.
        """
        if termination == 'high':
            spcm_dwSetParam_i64(self.hCard, SPC_TRIG_TERM, int64(0))
        elif termination == '50Ohm':
            spcm_dwSetParam_i64(self.hCard, SPC_TRIG_TERM, int64(1))
        else:
            print('Invalid main trigger termination.')
            sys.exit(1)

    def setMainTriggerInputCoupling(self, coupling):
        """
        Select the input coupling of the main trigger Trg0/Ext0. 
        Options are 'AC' and 'DC'.
        """
        if coupling == 'AC':
            spcm_dwSetParam_i32(self.hCard, SPC_TRIG_EXT0_ACDC, COUPLING_AC)
        elif coupling == 'DC':
            spcm_dwSetParam_i32(self.hCard, SPC_TRIG_EXT0_ACDC, COUPLING_DC)
        else:
            print("Invalid main trigger coupling.")
            sys.exit(1)

    def getAvailableMainTriggerModes(self):
        """
        Returns the available modes for the main trigger Trg0/Ext0 as a bitstring.
        """
        bitstring = int32(0)
        spcm_dwGetParam_i32(self.hCard, SPC_TRIG_EXT0_AVAILMODES, byref(bitstring))
        return bin(bitstring.value)

    def setMainTriggerMode(self, mode_str):
        """
        Set the mode of the main trigger Ext0/Trg0. Choose one of the following.
        'none': Disable channel
        'pos': Rising edge (crossing level 0 from below to above)
        'neg': Falling egde
        'pos_rearm': Only listen for trigger when crossing the re-arm level from below to above.
                        level0 is the trigger level and level1 the re-arm level. Trigger on rising edge.
                        Trigger has to be re-armed after every trigger event.
        'neg_rearm': Same as 'pos_rearm' but falling edge for both levels.
        'both': Rising and falling edge
        'high': Trigger when high (signal above level 0)
        'low': Trigger when low (signal below level 0)
        'window_enter': Window trigger for entering area between level 0 and level 1
        'window_leave': Window trigger for leaving area between level 0 and level 1
        'window_inside': window trigger for signal between level 0 and level 1
        'window_outside': window trigger for signal outside of area between level 0 and level 1
        """
        mode_dict = {'none': SPC_TM_NONE,\
                     'pos': SPC_TM_POS,\
                     'neg': SPC_TM_NEG,\
                     'pos_rearm': SPC_TM_REARM | SPC_TM_POS,\
                     'neg_rearm': SPC_TM_REARM | SPC_TM_NEG,\
                     'both': SPC_TM_BOTH,\
                     'high': SPC_TM_HIGH,\
                     'low': SPC_TM_LOW,\
                     'window_enter': SPC_TM_WINENTER,\
                     'window_leave': SPC_TM_WINLEAVE,\
                     'window_inside': SPC_TM_INWIN,\
                     'window_outside': SPC_TM_OUTSIDEWIN}
        mode = mode_dict[mode_str]
        spcm_dwSetParam_i32(self.hCard, SPC_TRIG_EXT0_MODE, mode)

    def getMainTriggerLevelInfo(self):
        """
        Return the min, max, and step of the main trigger level.
        """
        min = int32(0)
        spcm_dwGetParam_i32(self.hCard, SPC_TRIG_EXT_AVAIL0_MIN, byref(min))
        max = int32(0)
        spcm_dwGetParam_i32(self.hCard, SPC_TRIG_EXT_AVAIL0_MAX, byref(max))
        step = int32(0)
        spcm_dwGetParam_i32(self.hCard, SPC_TRIG_EXT_AVAIL0_STEP, byref(step))
        return min.value, max.value, step.value

    def setMainTriggerLevel(self, level0, level1):
        """
        Set the drigger levels in mV. Limits -10000 to 10000.
        Steps of 10. 
        """
        spcm_dwSetParam_i32(self.hCard, SPC_TRIG_EXT0_LEVEL0, int32(level0))
        spcm_dwSetParam_i32(self.hCard, SPC_TRIG_EXT0_LEVEL1, int32(level1))

    def getAvailableSecondaryTriggerModes(self):
        """
        Returns the available modes for the secondary trigger Trg1/Ext1 as a bitstring.
        """
        bitstring = int32(0)
        spcm_dwGetParam_i32(self.hCard, SPC_TRIG_EXT1_AVAILMODES, byref(bitstring))
        return bin(bitstring.value)

    def setSecondaryTriggerMode(self, mode_str):
        """
        Set the mode of the secondary trigger Ext1/Trg1. Choose one of the following.
        'none': Disable channel
        'pos': Rising edge (crossing level 0 from below to above)
        'neg': Falling egde
        'both': Rising and falling edge
        'high': Trigger when high (signal above level 0)
        'low': Trigger when low (signal below level 0)
        """
        mode_dict = {'none': SPC_TM_NONE,\
                     'pos': SPC_TM_POS,\
                     'neg': SPC_TM_NEG,\
                     'both': SPC_TM_BOTH,\
                     'high': SPC_TM_HIGH,\
                     'low': SPC_TM_LOW}
        mode = mode_dict[mode_str]
        spcm_dwSetParam_i32(self.hCard, SPC_TRIG_EXT1_MODE, mode)

    def getSecondaryTriggerLevelInfo(self):
        """
        Return the min, max, and step of the main trigger level.
        """
        min = int32(0)
        spcm_dwGetParam_i32(self.hCard, SPC_TRIG_EXT_AVAIL1_MIN, byref(min))
        max = int32(0)
        spcm_dwGetParam_i32(self.hCard, SPC_TRIG_EXT_AVAIL1_MAX, byref(max))
        step = int32(0)
        spcm_dwGetParam_i32(self.hCard, SPC_TRIG_EXT_AVAIL1_STEP, byref(step))
        return min.value, max.value, step.value

    def setSecondaryTriggerLevel(self, level0):
        """
        Set the drigger levels in mV. Limits -10000 to 10000.
        Steps of 10. 
        """
        spcm_dwSetParam_i32(self.hCard, SPC_TRIG_EXT1_LEVEL0, int32(level0))

    def setTriggerMaskOR(self, mode_tuple):
        """
        Setup the trigger mode for the OR mask. Possible modes are
        'none', 'software', 'ext0', 'ext1'. You can select as many options as you like,
        e.g. ('ext0', 'ext1').
        """
        mode_dict = {'none': SPC_TMASK_NONE,\
                     'software': SPC_TMASK_SOFTWARE,\
                     'ext0': SPC_TMASK_EXT0,\
                     'ext1': SPC_TMASK_EXT1}
        mode = [mode_dict[mode_str] for mode_str in mode_tuple]
        mode = reduce(ior, mode)
        spcm_dwSetParam_i32(self.hCard, SPC_TRIG_ORMASK, mode)

    def getTriggerMaskOR(self):
        """
        Get the bitstring for the trigger OR mask. 
        000: 'None'
        001: 'software'
        010: 'ext0'
        100: 'ext1'
        """
        bitstring = int32(0)
        spcm_dwGetParam_i32(self.hCard, SPC_TRIG_ORMASK, byref(bitstring))
        return bin(bitstring.value)

    def getAvailableTriggerModesOR(self):
        """
        Return the available trigger modes for the OR mask as bitstring. 
        You should get '0b111'.
        """
        bitstring = int64(0)
        spcm_dwGetParam_i64(self.hCard, SPC_TRIG_AVAILORMASK, byref(bitstring))
        return bin(bitstring.value)
    
    def setTriggerMaskAND(self, mode_tuple):
        """
        Setup the trigger mode for the AND mask. Possible modes are
        'none', 'softawre', 'ext0', 'ext1'. You can select as many options as you like,
        e.g. ('ext0', 'ext1').
        """
        mode_dict = {'none': SPC_TMASK_NONE,\
                     'software': SPC_TMASK_SOFTWARE,\
                     'ext0': SPC_TMASK_EXT0,\
                     'ext1': SPC_TMASK_EXT1}
        mode = [mode_dict[mode_str] for mode_str in mode_tuple]
        mode = reduce(ior, mode)
        spcm_dwSetParam_i32(self.hCard, SPC_TRIG_ANDMASK, mode)

    def getTriggerMaskAND(self):
        """
        Get the bitstring for the trigger AND mask. 
        000: 'None'
        001: 'software'
        010: 'ext0'
        100: 'ext1'
        """
        bitstring = int32(0)
        spcm_dwGetParam_i32(self.hCard, SPC_TRIG_ANDMASK, byref(bitstring))
        return bin(bitstring.value)
    
    def getAvailableTriggerModesAND(self):
        """
        Return the available trigger modes for the OR mask as bitstring. 
        You should get '0b110'.
        """
        bitstring = int64(0)
        spcm_dwGetParam_i64(self.hCard, SPC_TRIG_AVAILANDMASK, byref(bitstring))
        return bin(bitstring.value)
    
    def setTriggerDelay(self, delay_samples):
        """
        Configure the trigger delay in samples. The total delay is then delay_samples / sample_rate.
        Possible values are 0, 16, 32, ... , 8*(1024)**3-16
        """
        delay_samples = int64(delay_samples)
        spcm_dwSetParam_i64(self.hCard, SPC_TRIG_DELAY, delay_samples)
    
    def forceTrigger(self):
        """
        While the card is waiting for an external trigger signal, you can force a trigger event via software.
        """
        print('forced')
        spcm_dwSetParam_i32(self.hCard, SPC_M2CMD, M2CMD_CARD_FORCETRIGGER)

    def getTriggerDelay(self):
        """
        Return the trigger delay in seconds for the current configuration.
        Compute based on specifications on the data sheet.
        """
        return 238.5/(self.sampleRate*1e6) + 16e-9

    def armTrigger(self):
        """
        Arm the trigger system of the card.
        """
        print('armed')
        spcm_dwSetParam_i32(self.hCard, SPC_M2CMD, M2CMD_CARD_ENABLETRIGGER)

    def disarmTrigger(self):
        """
        Disarm the trigger system of the card.
        """
        spcm_dwSetParam_i32(self.hCard, SPC_M2CMD, M2CMD_CARD_DISABLETRIGGER)

    def setupAmplitudes(self, amp_ch1, amp_ch2):
        """
        Setup the amplitudes of the channels into 50 Ohm in mV.
        Valid setting are 80 to 2000.
        """
        spcm_dwSetParam_i32(self.hCard, SPC_AMP0, int32(amp_ch1))
        spcm_dwSetParam_i32(self.hCard, SPC_AMP1, int32(amp_ch2))

    def setupFilters(self, filter_ch1, filter_ch2):
        """
        Choose for each channel whether to use a filter.
        False: No filter
        True: 65 MHz filter.
        """
        spcm_dwSetParam_i32(self.hCard, SPC_FILTER0, filter_ch1)
        spcm_dwSetParam_i32(self.hCard, SPC_FILTER1, filter_ch2)

    def setupBuffer(self):
        """
        Try to allocate a continuous memory buffer for efficient data transfer.
        Use either continuous buffer or software allocated memory.
        """
        numActivatedChannels = self.getNumAvtivatedChannels()
        self.buffer_size = self.memory_size*self.bytesPerSample*numActivatedChannels
        countinuous_buffer_length = uint64(0)
        self.pointer_buffer = c_void_p()
        spcm_dwGetContBuf_i64(self.hCard, SPCM_BUF_DATA, byref(self.pointer_buffer), byref(countinuous_buffer_length))
        # print(self.pointer_buffer)

        # If we the continuous buffer is not large enough, we allocate memory using the program.
        if countinuous_buffer_length.value < self.buffer_size:
            self.pointer_buffer = pvAllocMemPageAligned(self.buffer_size)

    def uploadData(self):
        """
        Upload the data assigned to replay_data_ch1 and replay_data_ch2 to the card.
        """
        if self.ch1_enabled and (type(self.replay_data_ch1) == type(None)):
            print('No data for replay of channel 1 provided.')
            sys.exit(1)

        if self.ch2_enabled and (type(self.replay_data_ch2) == type(None)):
            print('No data for replay of channel 2 provided.')
            sys.exit(1)

        # Make sure everything is in int16
        if type(self.replay_data_ch1) == np.ndarray:
            data_ch1 = np.int16(self.replay_data_ch1)
        if type(self.replay_data_ch2) == np.ndarray:
            data_ch2 = np.int16(self.replay_data_ch2)
        
        # Get buffer in form that work with numpy
        data_buffer = np.frombuffer(self.pointer_buffer, dtype=c_short, count=-1)
        # print('data_buffer =', data_buffer)

        # Copy the data to the buffer
        if self.ch1_enabled and self.ch2_enabled:
            # Interleave data
            data_combined = np.zeros(self.buffer_size//2, dtype=np.int16) # Two bytes per sample
            data_combined[0::2] = data_ch1
            data_combined[1::2] = data_ch2
            np.copyto(data_buffer, data_combined)
        elif self.ch1_enabled and not self.ch2_enabled:
            np.copyto(data_buffer, data_ch1)

        elif not self.ch1_enabled and self.ch2_enabled:
            np.copyto(data_buffer, data_ch2)

        # DMA transfer
        print('Starting data transfer to onboard memory...')
        spcm_dwDefTransfer_i64(self.hCard, SPCM_BUF_DATA, SPCM_DIR_PCTOCARD, int32(0), self.pointer_buffer, uint64(0), self.buffer_size)
        spcm_dwSetParam_i32(self.hCard, SPC_M2CMD, M2CMD_DATA_STARTDMA | M2CMD_DATA_WAITDMA) 
        print('Data transfer complete.')

    def startReplay(self):
        """
        Arms the trigger and starts the replay.
        """
        print('Starting replay.')
        spcm_dwSetParam_i32(self.hCard, SPC_M2CMD, M2CMD_CARD_START | M2CMD_CARD_WAITREADY | M2CMD_CARD_ENABLETRIGGER)

    def waitReady(self):
        """
        Waits until the replay has completed the current run. This also returns once the output has stopped.
        """
        spcm_dwSetParam_i32(self.hCard, SPC_M2CMD, M2CMD_CARD_WAITREADY)

    def waitTrigger(self):
        """
        Wait until a trigger event is detected by the card.
        """
        spcm_dwSetParam_i32(self.hCard, SPC_M2CMD, M2CMD_CARD_WAITTRIGGER)

    def resetCard(self):
        """
        Reset all the settings to default values defined by the manufacturer.
        These can be different from your chosen default values!
        """
        spcm_dwSetParam_i32(self.hCard, SPC_M2CMD, M2CMD_CARD_RESET)

    def getStart(self): #(added by Andrea)
        """
        Set the board ready.
        """
        print('Set Ready.')
        spcm_dwSetParam_i32(self.hCard, SPC_M2CMD, M2CMD_CARD_START)

    def setTimeout(self, Timeout): #(added by Andrea)
        """
        Set the timout before stop waiting for trigger.
        """ 
        spcm_dwSetParam_i32(self.hCard, SPC_TIMEOUT, Timeout)

if __name__ == '__main__':
    mycard = SpectrumCardInterface()  
    mycard.ch1_enabled = True
    mycard.ch2_enabled = True
    # Configure the data
    mycard.num_loops = 1000 #10000*1
    mycard.memory_size = 1024
    mycard.sampleRate = 625

    time = np.linspace(0, mycard.memory_size/(mycard.sampleRate*1e6), mycard.memory_size)

    freq_ch1 = 50e6
    amplitude_ch1 = 1
    phase_ch1 = 0
    mycard.amplitude_ch1 = 158

    data_ch1 = amplitude_ch1*np.sin(2*np.pi*freq_ch1*time+phase_ch1)
    data_ch1 /= np.amax(data_ch1)
    data_ch1 = data_ch1 * (2**15-1) # MISSES THE MOST NEGATIVE SETTING


    freq_ch2 = freq_ch1
    amplitude_ch2 = 1
    phase_ch2 = 0
    mycard.amplitude_ch2 = mycard.amplitude_ch1

    data_ch2 = amplitude_ch2*np.sin(2*np.pi*freq_ch2*time+phase_ch2)
    data_ch2 /= np.amax(data_ch2)
    data_ch2 = data_ch2 * (2**15-1) # MISSES THE MOST NEGATIVE SETTING

    # Set the replay data
    mycard.replay_data_ch1 = data_ch1
    mycard.replay_data_ch2 = data_ch2

    mycard.setupCard()
    mycard.startReplay()
    
    mycard.closeCard()

