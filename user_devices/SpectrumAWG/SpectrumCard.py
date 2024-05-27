# First own code to run the spectrum card
# Marvin 08.03.2024

from .pyspcm import *
from .spcm_tools import *
import ctypes
import numpy as np



class SpectrumCard:

    def __init__(self, device_path='/dev/spcm0', timeout = 5000):
        """
        Class constructor.
        """
        self.device_path = device_path
        self.hCard = None
        self.timeout = timeout

    def __del__(self):
        """
        Destructor method to ensure the connection is closed when the class instance is destroyed.
        """
        self.card_close()  # Call the close method to safely close the connection if it's still open

    def open(self):
        """
        Open handle to the Spectrum AWG card.

        Parameters:
        - timeout: Defines the timeout for any following wait command in a millisecond resolution. Writing a zero disables the timeout.

        """
        card_type_names = {
        SPCM_TYPE_AI: "analog input",
        SPCM_TYPE_AO: "analog output",
        SPCM_TYPE_DI: "digital input",
        SPCM_TYPE_DO: "digital output",
        SPCM_TYPE_DIO: "digital I/O"
        }
        # check that card is not already opened
        if self.hCard is not None:
            self.card_close()

        # open card reference
        self.hCard = spcm_hOpen(create_string_buffer(self.device_path.encode()))
        if not self.hCard:
            print("no card found...\n")
            exit(1)
        # get card type name and serial number from driver
        qwValueBufferLen = 20
        pValueBuffer = pvAllocMemPageAligned(qwValueBufferLen)
        spcm_dwGetParam_ptr(self.hCard, SPC_PCITYP, pValueBuffer, qwValueBufferLen)
        sCardName = pValueBuffer.value.decode('UTF-8')
        lSerialNumber = int64(0)
        spcm_dwGetParam_i64(self.hCard, SPC_PCISERIALNO, byref(lSerialNumber))
        print("Found: {0} with S/N: {1:05d}\n".format(sCardName, lSerialNumber.value))
        self.serial = lSerialNumber.value
        self.name = sCardName

        # Check Card Type
        lFncType = int64(0)
        spcm_dwGetParam_i64(self.hCard, SPC_FNCTYPE, byref(lFncType))
        print("The card is an "+ card_type_names.get(lFncType.value, "unknown card type") + " card." )
        self.type = card_type_names.get(lFncType.value, "unknown card type")
        
        # Check Memory on the card
        lMemSize = int64(0)
        spcm_dwGetParam_i64(self.hCard, SPC_PCIMEMSIZE, byref(lMemSize))
        print(f"There are {self.format_to_si(lMemSize.value)}bytes of memory on the card.")
        self.memSize = lMemSize.value

        # Get Limits for Sequence replay
        self.seq_get_setting_limits()

        # Set timeout
        spcm_dwSetParam_i64(self.hCard, SPC_TIMEOUT, self.timeout)

        self.handle_error()

    def print_available_pci_features(self):
        """
        Reads the PCI feature register and prints out all installed features and options as a bitfield.
        """
        features_bitmask = int32(0)
        result = spcm_dwGetParam_i32(self.hCard, SPC_PCIFEATURES, byref(features_bitmask))
        if result != ERR_OK:
            print("Failed to read PCI features.")
            self.handle_error()  # Assuming handleError is your function for error handling
            return
        
        # Define all possible features and their bitmask values
        features = {
            "Multiple Recording / Multiple Replay": SPCM_FEAT_MULTI,
            "Gated Sampling / Gated Replay": SPCM_FEAT_GATE,
            "Digital Inputs / Digital Outputs": SPCM_FEAT_DIGITAL,
            "Timestamp": SPCM_FEAT_TIMESTAMP,
            "Star-Hub (up to 6 cards)": SPCM_FEAT_STARHUB6_EXTM,
            "Star-Hub (up to 8 cards, M4i)": SPCM_FEAT_STARHUB8_EXTM,
            "Star-Hub (up to 4 cards)": SPCM_FEAT_STARHUB4,
            "Star-Hub (up to 5 cards)": SPCM_FEAT_STARHUB5,
            "Star-Hub (up to 16 cards, M2p)": SPCM_FEAT_STARHUB16_EXTM,
            "Star-Hub (up to 8 cards, M3i and M5i)": SPCM_FEAT_STARHUB8,
            "Star-Hub (up to 16 cards, M2i)": SPCM_FEAT_STARHUB16,
            "ABA Mode": SPCM_FEAT_ABA,
            "BaseXIO Option": SPCM_FEAT_BASEXIO,
            "Amplifier 10V": SPCM_FEAT_AMPLIFIER_10V,
            "System Star-Hub Master": SPCM_FEAT_STARHUBSYSMASTER,
            "Differential Mode": SPCM_FEAT_DIFFMODE,
            "Replay Sequence Mode": SPCM_FEAT_SEQUENCE,
            "Amplifier Module 10V": SPCM_FEAT_AMPMODULE_10V,
            "System Star-Hub Slave": SPCM_FEAT_STARHUBSYSSLAVE,
            "DigitizerNETBOX": SPCM_FEAT_NETBOX,
            "Remote Server Support": SPCM_FEAT_REMOTESERVER,
            "SCAPP Option": SPCM_FEAT_SCAPP,
            "Digital I/Os via SMB (M2p)": SPCM_FEAT_DIG16_SMB,
            "Digital I/Os via FX2 (M2p)": SPCM_FEAT_DIG16_FX2,
            "Digital Bandwidth Filter": SPCM_FEAT_DIGITALBWFILTER,
        }

        print("Available PCI Features:")
        for feature_name, bitmask in features.items():
            if features_bitmask.value & bitmask:
                print(f"- {feature_name}")

        # Check for custom modifications
        custom_mod_mask = 0xF0000000
        if features_bitmask.value & custom_mod_mask:
            print("- Custom Modifications: Yes")
        else:
            print("- Custom Modifications: No")

    def seq_get_setting_limits(self):
        """
        Reads sequence settings from the card and stores them in the class.
        """
        # Preparing variables to hold the settings values
        max_segments = ctypes.c_int32()
        max_steps = ctypes.c_int32()
        max_loops = ctypes.c_int32()

        # Read the maximum number of segments, steps, and loops from their respective registers
        spcm_dwGetParam_i32(self.hCard, SPC_SEQMODE_AVAILMAXSEGMENT, ctypes.byref(max_segments))
        spcm_dwGetParam_i32(self.hCard, SPC_SEQMODE_AVAILMAXSTEPS, ctypes.byref(max_steps))
        spcm_dwGetParam_i32(self.hCard, SPC_SEQMODE_AVAILMAXLOOP, ctypes.byref(max_loops))

        # Store the read values in the class attributes
        self.seq_max_segments = max_segments.value
        self.seq_max_steps = max_steps.value
        self.seq_max_loops = max_loops.value

    def handle_error(self):
        """
        Handle error of the Spectrum card and print error text.

        """
        errorText = create_string_buffer(ERRORTEXTLEN)
        if spcm_dwGetErrorInfo_i64(self.hCard, None, None, byref(errorText)) != ERR_OK: # check for an error
            print(errorText.value.decode()) # print the error text
            spcm_vClose(self.hCard) # close the driver
            exit (0) # and leave the program

    def set_clock(self, mode = 'internal', frequency = None):
        """
        Set the clock mode of the Spectrum card to either external or internal.

        Parameters:
        - mode: A string indicating the desired clock mode, either 'internal' or 'external'.
        - frequency: The frequency of the external reference clock.
        """
        if mode == 'internal':
            mode_value = SPC_CM_INTPLL
        elif mode == 'external':
            mode_value = SPC_CM_EXTREFCLOCK
            if frequency is None:
                raise ValueError("Frequency must be specified for external clock mode.")
            spcm_dwSetParam_i32(self.hCard, SPC_REFERENCECLOCK, frequency)
            print(f"External clock set to {self.format_to_si(frequency)}Hz.")
            self.extClkRate = frequency
        else:
            raise ValueError("Invalid mode specified. Use 'internal' or 'external'.")

        # Set the clock mode
        result = spcm_dwSetParam_i32(self.hCard, SPC_CLOCKMODE, mode_value)
        if result != ERR_OK:
            print(f"Failed to set clock mode to {mode}.")
            self.handle_error()  # Assuming handleError is your function for error handling
        else:
            print(f"Clock mode set to {mode} successfully.")

    def set_sample_rate(self, sample_rate):
        """
        Set the sample rate of the Spectrum card.

        Parameters:
        - sample_rate: The desired sample rate in Samples per second.
        """
        # Set the sample rate. Adjust SPC_SAMPLERATE to your API's correct parameter name
        result = spcm_dwSetParam_i32(self.hCard, SPC_SAMPLERATE, sample_rate)
        if result != ERR_OK:
            print(f"Failed to set sample rate to {self.format_to_si(sample_rate)}S/s .")
            self.handle_error()
        else:
            print(f"Sample rate set to {self.format_to_si(sample_rate)}S/s successfully.")
            self.sampelRate = sample_rate

    @staticmethod
    def format_to_si(number):
        """
        Convert a number to a string with the appropriate engineering notation (K, M, G).

        Parameters:
        - number: The number to convert.

        Returns:
        - A string with the appropriate unit (e.g., "100 M").
        """
        if number >= 1e12:  # Tera
            formatted_rate = f"{number / 1e12:g} T"
        elif number >= 1e9:  # Giga
            formatted_rate = f"{number / 1e9:g} G"
        elif number >= 1e6:  # Mega
            formatted_rate = f"{number / 1e6:g} M"
        elif number >= 1e3:  # Kilo
            formatted_rate = f"{number / 1e3:g} k"
        else:
            formatted_rate = f"{number:g} "

        return formatted_rate

    def set_channel_status(self, channel_number, channel_status = False):
        """
        Turns channels 1 and 2 on or off on the Spectrum card.

        Parameters:
        - channel_number: Number of the channel (0 ... 3) to set.
        - channel_status: Boolean indicating the desired status for the channel (True for on, False for off).
        """
        # Read number of channels of the card
        buff = int64(0)
        spcm_dwGetParam_i64(self.hCard, SPC_MIINST_CHPERMODULE, byref(buff))
        self.channels_available = buff.value
        

        # Validate channel_number input
        if channel_number < 0 or channel_number >= self.channels_available:
            raise ValueError(f"Invalid channel number. Channel number must be between 0 and {self.channels_available-1}.")

        # Current bitmask for channel enable status
        current_status = int64(0)
        spcm_dwGetParam_i64(self.hCard, SPC_CHENABLE, byref(current_status))

        # Calculate the new bitmask based on desired channel statuses
        # Note: Adjust the bit manipulation as necessary based on your card's documentation
        new_status = current_status.value
        if channel_status:
            new_status |= (1 << channel_number)  # Set bit channel_number to enable channel 1
        else:
            new_status &= ~(1 << channel_number)  # Clear bit channel_number to disable channel 1

        # Apply the new channel enable status
        result = spcm_dwSetParam_i64(self.hCard, SPC_CHENABLE, new_status)
        if result != ERR_OK:
            print(result)
            print("Failed to set channel status.")
            self.handle_error()
        else:
            # Retrieve and print the updated channel statuses
            spcm_dwGetParam_i64(self.hCard, SPC_CHENABLE, byref(current_status))
            print("Updated channel statuses:")
            for i in range(self.channels_available):  # Print all channels statuses
                channel_is_on = bool(current_status.value & (1 << i))
                print(f"Channel {i}: {'On' if channel_is_on else 'Off'}")
            
            spcm_dwGetParam_i64(self.hCard, SPC_CHCOUNT, byref(buff))
            channels_active = buff.value
            print(f"The card reports a total of {channels_active} active channels.")

    def set_channel_enable(self, output_number, enable):
        """
        Enables or disables the output of a specified channel on the Spectrum card using predefined variables.

        Parameters:
        - output_number: The output number (0 ... 3).
        - enable: Boolean indicating whether to enable (True) or disable (False) the output.
        """
        # Mapping of output numbers to their respective SPC_ENABLEOUT variables
        output_registers = {
            0: SPC_ENABLEOUT0,
            1: SPC_ENABLEOUT1,
            2: SPC_ENABLEOUT2,
            3: SPC_ENABLEOUT3
        }

        # Validate output_number input
        if output_number not in output_registers or output_number >= self.channels_available:
            raise ValueError(f"Invalid output number. Must be between 0 and {self.channels_available-1}.")
        
        # Get the correct register for the specified output
        register = output_registers[output_number]

        # Set the enable/disable register for the specified output
        result = spcm_dwSetParam_i32(self.hCard, register, c_int32(int(enable)))
        if result != ERR_OK:
            print(f"Failed to {'enable' if enable else 'disable'} output channel {output_number}.")
            self.handle_error()  # Handle errors appropriately
        else:
            print(f"Output of channel {output_number} {'enabled' if enable else 'disabled'} successfully.")

    def set_channel_amplitude(self, output_number, amplitude_mV):
        """
        Sets the output amplitude for a specified channel.

        Parameters:
        - channel_number: The channel number (0 to 3).
        - amplitude_mV: Desired amplitude in mV (80 to 2500 for certain channels, 80 to 2000 for others).
        """

        output_registers = {
            0: SPC_AMP0,
            1: SPC_AMP1,
            2: SPC_AMP2,
            3: SPC_AMP3
        }

        # Validate input parameters
        if output_number not in output_registers or output_number >= self.channels_available:
            raise ValueError(f"Invalid output number. Must be between 0 and {self.channels_available-1}.")
        
        if self.name == 'M4i.6631-x8' or self.name == 'M4i.6630-x8':
            maxVoltage = 2000
        else:
            maxVoltage = 2500


        if not 80 <= amplitude_mV <= maxVoltage:  # Adjust the upper limit if needed for specific channels
            raise ValueError(f"Amplitude out of allowed range. Must be between 80 and {maxVoltage} mV.")

        # Get the correct register for the specified output
        register = output_registers[output_number]

        # Set the amplitude register for the specified channel
        result = spcm_dwSetParam_i32(self.hCard, register, amplitude_mV)
        if result != ERR_OK:
            print(f"Failed to set amplitude for channel {output_number}.")
            self.handle_error()  # Assume handleError is a method for error handling
        else:
            print(f"Amplitude for channel {output_number} set to {amplitude_mV} mV successfully.")

    def set_channel_filter(self, output_number, filter_setting):
        """
        Sets the filter setting for a specified channel on the Spectrum card.

        Parameters:
        - output_number: The output number (0 ... 3).
        - filter_setting: The filter setting to apply (specific value or mode).
        """
        # Mapping of output numbers to their respective filter setting registers
        filter_registers = {
            0: SPC_FILTER0,
            1: SPC_FILTER1,
            2: SPC_FILTER2,
            3: SPC_FILTER3
        }

        # Validate output_number input
        if output_number not in filter_registers or output_number >= self.channels_available:
            raise ValueError(f"Invalid output number. Must be between 0 and {self.channels_available-1}.")

        # Get the correct register for the specified output's filter setting
        register = filter_registers[output_number]

        # Set the filter register for the specified output
        result = spcm_dwSetParam_i32(self.hCard, register, c_int32(filter_setting))
        if result != ERR_OK:
            print(f"Failed to set filter for output channel {output_number}.")
            self.handle_error()  # Assuming handleError is your method for error handling
        else:
            print(f"Filter for channel {output_number} {'enabled' if filter_setting else 'disabled'} succesfully.")

    def set_channel_mode(self,channel_number , mode=None):
        """
        Sets the mode for a specified channel on the Spectrum card.

        Parameters:
        - channel_number: The number of the channel to configure (e.g., 0, 1, 2).
        - mode: The output mode of the channel:
            - None: Single-ended mode.
            - 'diff': The channel is set as a differential output.
            - 'double': The channel output is copied.
        """
        # Example mapping of modes to registers for each channel. Adjust based on actual API.
        mode_registers = {
            0: {'diff': SPC_DIFF0, 'double': SPC_DOUBLEOUT0},
            1: {'diff': SPC_DIFF0, 'double': SPC_DOUBLEOUT1},
            2: {'diff': SPC_DIFF2, 'double': SPC_DOUBLEOUT2},
        }

        if channel_number not in mode_registers or mode not in ['diff', 'double', None]:
            raise ValueError("Invalid channel number or mode specified.")
        
        # Make sure all the modes are off before applying the new setting.
        spcm_dwSetParam_i32(self.hCard, mode_registers[channel_number]['diff'], 0)
        spcm_dwSetParam_i32(self.hCard, mode_registers[channel_number]['double'], 0)

        if mode is None:
            print(f"Channel {channel_number} set to default mode.")
            return

        # Get the correct register for the specified channel and mode
        register = mode_registers[channel_number][mode]

        # Assuming 1 is the value to enable the mode. Adjust as per your device's requirements.
        result = spcm_dwSetParam_i32(self.hCard, register, 1)
        if result != ERR_OK:
            print(f"Failed to set channel {channel_number} to mode '{mode}'.")
            self.handle_error()  # Handle errors appropriately
        else:
            print(f"Channel {channel_number} set to mode '{mode}' successfully.")

    def set_generation_mode(self,mode):
        """
        Sets the signal generation mode of the card.
        Parameters:
        - mode: Replay mode of the DAC
            'single': Data generation from on-board memory repeating the complete programmed memory either once, infinite or for a defined number of times after one single trigger event.
            'multi': Data generation from on-board memory for multiple trigger events.
            'gated': Data generation from on-board memory using an external gate signal. Data is only generated as long as the gate signal has a programmed level.
            'single_trg': Data generation from on-board memory. The programmed memory is repeated once after each single trigger event.
            'sequence': Data generation from on-board memory splitting the memory into several segments and replaying the data using a special sequence memory.
            'fifo_single': Continuous data generation after one single trigger event. The on-board memory is used completely as FIFO buffer.
            'fifo_multi':  Continuous data generation after multiple trigger events. The on-board memory is used completely as FIFO buffer.
            'fifo_gate': Continuous data generation using an external gate signal. The on-board memory is used completely as FIFO buffer.
            'dds': DDS replay mode functionality available (firmware option required).
        """
        buff = int64(0)
        spcm_dwGetParam_i32(self.hCard,SPC_AVAILCARDMODES,byref(buff))
        available_modes= buff.value

        replay_modes = {
            'single': SPC_REP_STD_SINGLE,
            'multi': SPC_REP_STD_MULTI,
            'gated': SPC_REP_STD_GATE,
            'single_trg': SPC_REP_STD_SINGLERESTART,
            'sequence': SPC_REP_STD_SEQUENCE,
            'fifo_single': SPC_REP_FIFO_SINGLE,
            'fifo_multi': SPC_REP_FIFO_MULTI,
            'fifo_gate': SPC_REP_FIFO_GATE,
            'dds': SPC_REP_STD_DDS,
        }

        if mode not in replay_modes:
            print(f"Invalid mode specified: {mode}")
            return

        # Get the correct bitmap for the selected mode
        mode_register_value = replay_modes[mode]

        # Check if the mode is available by performing a bitwise AND with the available modes bitmap
        if available_modes & mode_register_value:
            spcm_dwSetParam_i32(self.hCard, SPC_CARDMODE, mode_register_value)
            print(f"Generation mode set to '{mode}'.")
        else:
            print(f"The mode '{mode}' is not available on this card.")

    def set_ext_trigger_mode(self, channel, mode, rearm=False):
        """
        Sets the trigger mode for the specified external trigger input (Ext0 or Ext1).

        Parameters:
        - channel: The external trigger channel to configure ('ext0' or 'ext1').
        - mode: The trigger mode to set. Can be 'pos', 'neg', 'both', 'high', 'low', 'win_enter', 'win_leave', 'in_win', 'outside_win'.
        - rearm: Boolean indicating whether to use rearming for edge triggers to avoid false triggers on noise.
        """
        # Validate the channel selection
        if channel not in ['ext0', 'ext1']:
            raise ValueError("Invalid external trigger channel specified. Choose 'ext0' or 'ext1'.")

        # Map the mode to the corresponding register values
        mode_mapping = {
            'pos': SPC_TM_POS,
            'neg': SPC_TM_NEG,
            'both': SPC_TM_BOTH,
            'high': SPC_TM_HIGH,
            'low': SPC_TM_LOW,
            'win_enter': SPC_TM_WINENTER,
            'win_leave': SPC_TM_WINLEAVE,
            'in_win': SPC_TM_INWIN,
            'outside_win': SPC_TM_OUTSIDEWIN,
        }

        if mode not in mode_mapping:
            raise ValueError("Invalid trigger mode specified.")

        trigger_mode = mode_mapping[mode]

        if rearm and mode in ['pos', 'neg']:
            trigger_mode |= SPC_TM_REARM

        # Adjust the register constants based on the selected channel
        trig_mode_register = SPC_TRIG_EXT0_MODE if channel == 'ext0' else SPC_TRIG_EXT1_MODE

        # Write the trigger mode to the appropriate external trigger mode register
        result = spcm_dwSetParam_i32(self.hCard, trig_mode_register, trigger_mode)
        if result != ERR_OK:
            print(f"Failed to set {channel} trigger mode to {mode}.")
            self.handle_error()  # Assuming handleError is your function for error handling
        else:
            print(f"{channel.upper()} trigger mode set to {mode}{' with rearming' if rearm else ''} successfully.")

    def print_available_ext_trigger_modes(self):
        """
        Reads and prints out all available trigger modes for the external trigger input Ext0.
        """
        # Dictionary mapping trigger mode bitmasks to human-readable descriptions
        trigger_mode_descriptions = {
            SPC_TM_NONE: "None",
            SPC_TM_POS: "Positive edge",
            SPC_TM_NEG: "Negative edge",
            SPC_TM_POS | SPC_TM_REARM: "Positive edge with rearming",
            SPC_TM_NEG | SPC_TM_REARM: "Negative edge with rearming",
            SPC_TM_BOTH: "Both edges",
            SPC_TM_HIGH: "High level",
            SPC_TM_LOW: "Low level",
            SPC_TM_WINENTER: "Window enter",
            SPC_TM_WINLEAVE: "Window leave",
            SPC_TM_INWIN: "Inside window",
            SPC_TM_OUTSIDEWIN: "Outside window",
        }

        # Read the available trigger modes bitmask
        avail_modes = int32(0)
        result = spcm_dwGetParam_i32(self.hCard, SPC_TRIG_EXT0_AVAILMODES, byref(avail_modes))
        if result != ERR_OK:
            print("Failed to read available external trigger modes.")
            self.handle_error()  # Assuming handleError is your function for error handling
            return

        print("Available External Trigger Modes for Ext0:")
        # Iterate through each possible mode and check if it's available
        for mode, description in trigger_mode_descriptions.items():
            if avail_modes.value & mode:
                print(f"- {description}")

    def print_ext_trigger_level_range(self, channel):
        """
        Prints the available trigger level settings for the specified external trigger channel.
    
        Parameters:
        - channel: The external trigger channel ('ext0' or 'ext1').
        """
        if channel not in ['ext0', 'ext1']:
            raise ValueError("Invalid external trigger channel specified. Choose 'ext0' or 'ext1'.")
    
        base = SPC_TRIG_EXT_AVAIL0_MIN if channel == 'ext0' else SPC_TRIG_EXT_AVAIL1_MIN  # Base register for the channel
    
        min_level = int32(0)
        max_level = int32(0)
        step_size = int32(0)
    
        # Read the available range and step size
        spcm_dwGetParam_i32(self.hCard, base, byref(min_level))
        spcm_dwGetParam_i32(self.hCard, base + 1, byref(max_level))
        spcm_dwGetParam_i32(self.hCard, base + 2, byref(step_size))
    
        print(f"Available trigger level range for {channel.upper()}:")
        print(f"Min: {min_level.value} mV")
        print(f"Step size: {step_size.value} mV")
        print(f"Max: {max_level.value} mV")

    def set_ext_trigger_level(self, channel, level0, level1):
        """
        Sets the trigger levels for the specified external trigger channel.

        Parameters:
        - channel: The external trigger channel ('ext0' or 'ext1').
        - level: The trigger level to set in mV.
        """
        if channel not in ['ext0', 'ext1']:
            raise ValueError("Invalid external trigger channel specified. Choose 'ext0' or 'ext1'.")

        level0_register = SPC_TRIG_EXT0_LEVEL0 if channel == 'ext0' else SPC_TRIG_EXT1_LEVEL0
        level1_register = SPC_TRIG_EXT0_LEVEL1 if channel == 'ext0' else SPC_TRIG_EXT1_LEVEL1

        # Set the trigger level0
        result = spcm_dwSetParam_i32(self.hCard, level0_register, int32(level0))
        if result != ERR_OK:
            print(f"Failed to set trigger level 0 for {channel} to {level0} mV.")
            self.handle_error()  # Assuming handleError is your function for error handling
        else:
            print(f"Trigger level 0 for {channel.upper()} set to {level0} mV successfully.")

        # Set the trigger level1
        result = spcm_dwSetParam_i32(self.hCard, level1_register, int32(level1))
        if result != ERR_OK:
            print(f"Failed to set trigger level 1 for {channel} to {level1} mV.")
            self.handle_error()  # Assuming handleError is your function for error handling
        else:
            print(f"Trigger level 1 for {channel.upper()} set to {level1} mV successfully.")

    def print_available_or_trigger_sources(self):
        """
        Reads and prints out all available trigger sources for the OR mask.
        """
        # Mapping of bitmask values to human-readable trigger source names
        mask_to_source = {
            SPC_TMASK_SOFTWARE: "Software",
            SPC_TMASK_EXT0: "External trigger EXT0",
            SPC_TMASK_EXT1: "External trigger EXT1",
            SPC_TMASK_PXI0: "PXI_TRIG0",
            SPC_TMASK_PXI1: "PXI_TRIG1",
            SPC_TMASK_PXI2: "PXI_TRIG2",
            SPC_TMASK_PXI3: "PXI_TRIG3",
            SPC_TMASK_PXI4: "PXI_TRIG4",
            SPC_TMASK_PXI5: "PXI_TRIG5",
            SPC_TMASK_PXI6: "PXI_TRIG6",
            SPC_TMASK_PXI7: "PXI_TRIG7",
            SPC_TMASK_PXISTAR: "PXISTAR",
            SPC_TMASK_PXIDSTARB: "PXI_DSTARB",
        }

        # Read the available OR mask sources bitmask
        avail_or_mask = int32(0)
        result = spcm_dwGetParam_i32(self.hCard, SPC_TRIG_AVAILORMASK, byref(avail_or_mask))
        if result != ERR_OK:
            print("Failed to read available trigger sources for the OR mask.")
            self.handle_error()  # Assuming handleError is your function for error handling
            return

        print("Available Trigger Sources for the OR Mask:")
        for mask, source_name in mask_to_source.items():
            if avail_or_mask.value & mask:
                print(f"- {source_name}")

    def set_trigger_or_mask(self, enable_sources):
        """
        Sets the trigger OR mask by enabling specified trigger sources.

        Parameters:
        - enable_sources: A list of strings indicating which trigger sources to enable. 
                          Valid strings: 'software', 'ext0', 'ext1', 'pxi0' to 'pxi7', 'pxistar', 'pxidstarb'
        """
        # Mapping from trigger source strings to bitmask values
        source_to_mask = {
            'software': SPC_TMASK_SOFTWARE,
            'ext0': SPC_TMASK_EXT0,
            'ext1': SPC_TMASK_EXT1,
            'pxi0': SPC_TMASK_PXI0,
            'pxi1': SPC_TMASK_PXI1,
            'pxi2': SPC_TMASK_PXI2,
            'pxi3': SPC_TMASK_PXI3,
            'pxi4': SPC_TMASK_PXI4,
            'pxi5': SPC_TMASK_PXI5,
            'pxi6': SPC_TMASK_PXI6,
            'pxi7': SPC_TMASK_PXI7,
            'pxistar': SPC_TMASK_PXISTAR,
            'pxidstarb': SPC_TMASK_PXIDSTARB,
        }

        # Start with no trigger sources selected
        or_mask = SPC_TMASK_NONE

        # Iterate through the requested sources, adding them to the OR mask
        for source in enable_sources:
            if source in source_to_mask:
                or_mask |= source_to_mask[source]
            else:
                print(f"Warning: Ignoring unrecognized trigger source '{source}'.")

        # Write the OR mask to the card
        result = spcm_dwSetParam_i32(self.hCard, SPC_TRIG_ORMASK, or_mask)
        if result != ERR_OK:
            print("Failed to set trigger OR mask.")
            self.handle_error()  # Assuming handleError is your function for error handling
        else:
            print("Trigger OR mask set successfully.")

    def print_available_and_trigger_sources(self):
        """
        Reads and prints out all available trigger sources for the AND mask.
        """
        mask_to_source = {
            SPC_TMASK_EXT0: "External trigger EXT0",
            SPC_TMASK_EXT1: "External trigger EXT1",
            SPC_TMASK_PXI0: "PXI_TRIG0",
            SPC_TMASK_PXI1: "PXI_TRIG1",
            SPC_TMASK_PXI2: "PXI_TRIG2",
            SPC_TMASK_PXI3: "PXI_TRIG3",
            SPC_TMASK_PXI4: "PXI_TRIG4",
            SPC_TMASK_PXI5: "PXI_TRIG5",
            SPC_TMASK_PXI6: "PXI_TRIG6",
            SPC_TMASK_PXI7: "PXI_TRIG7",
            SPC_TMASK_PXISTAR: "PXISTAR",
            SPC_TMASK_PXIDSTARB: "PXI_DSTARB",
        }

        avail_and_mask = int32(0)
        result = spcm_dwGetParam_i32(self.hCard, SPC_TRIG_AVAILANDMASK, byref(avail_and_mask))
        if result != ERR_OK:
            print("Failed to read available trigger sources for the AND mask.")
            self.handle_error()  # Assuming handleError is your function for error handling
            return

        print("Available Trigger Sources for the AND Mask:")
        for mask, source_name in mask_to_source.items():
            if avail_and_mask.value & mask:
                print(f"- {source_name}")

    def set_trigger_and_mask(self, enable_sources):
        """
        Sets the trigger AND mask by enabling specified trigger sources.

        Parameters:
        - enable_sources: A list of strings indicating which trigger sources to enable.
        """
        source_to_mask = {
            'ext0': SPC_TMASK_EXT0,
            'ext1': SPC_TMASK_EXT1,
            'pxi0': SPC_TMASK_PXI0,
            'pxi1': SPC_TMASK_PXI1,
            'pxi2': SPC_TMASK_PXI2,
            'pxi3': SPC_TMASK_PXI3,
            'pxi4': SPC_TMASK_PXI4,
            'pxi5': SPC_TMASK_PXI5,
            'pxi6': SPC_TMASK_PXI6,
            'pxi7': SPC_TMASK_PXI7,
            'pxistar': SPC_TMASK_PXISTAR,
            'pxidstarb': SPC_TMASK_PXIDSTARB,
        }

        and_mask = SPC_TMASK_NONE  # Start with no trigger sources selected

        for source in enable_sources:
            if source in source_to_mask:
                and_mask |= source_to_mask[source]
            else:
                print(f"Warning: Ignoring unrecognized trigger source '{source}'.")

        result = spcm_dwSetParam_i32(self.hCard, SPC_TRIG_ANDMASK, and_mask)
        if result != ERR_OK:
            print("Failed to set trigger AND mask.")
            self.handle_error()
        else:
            print("Trigger AND mask set successfully.")

    def card_reset(self):
        """Performs a hard and software reset of the card."""
        spcm_dwSetParam_i32(self.hCard, SPC_M2CMD , M2CMD_CARD_RESET)
        self.handle_error()
        print("Card has been reset.")

    def card_write_setup(self):
        """Writes the current setup to the card without starting the hardware."""
        spcm_dwSetParam_i32(self.hCard, SPC_M2CMD , M2CMD_CARD_WRITESETUP)
        self.handle_error()        
        print("Card setup written.")

    def card_start(self):
        """Starts the card with all selected settings. This command automatically writes all settings to the card."""
        spcm_dwSetParam_i32(self.hCard, SPC_M2CMD , M2CMD_CARD_START)
        self.handle_error()        
        print("Card started.")

    def card_enable_trigger(self):
        """The trigger detection is enabled. This command can be sent together with the start command or after some external hardware has been started."""
        spcm_dwSetParam_i32(self.hCard, SPC_M2CMD , M2CMD_CARD_ENABLETRIGGER)
        self.handle_error()
        print("Trigger enabled.")

    def card_force_trigger(self):
        """This command forces a trigger even if none has been detected so far. Similar to using the software trigger."""
        spcm_dwSetParam_i32(self.hCard, SPC_M2CMD , M2CMD_CARD_FORCETRIGGER)
        self.handle_error()        
        print("Software trigger.")

    def card_disable_trigger(self):
        """The trigger detection is disabled. All further trigger events are ignored until the trigger detection is again enabled."""
        spcm_dwSetParam_i32(self.hCard, SPC_M2CMD , M2CMD_CARD_DISABLETRIGGER)
        self.handle_error()         
        print("Trigger disabled.")

    def card_stop(self):
        """Stops the current run of the card. If the card is not running, this command has no effect."""
        spcm_dwSetParam_i32(self.hCard, SPC_M2CMD , M2CMD_CARD_STOP)
        self.handle_error()        
        print("Card stopped.")

    def card_wait_ready(self):
        """Waits until the card has completed the current run. In a generation mode receiving this command means that the output has stopped."""
        spcm_dwSetParam_i32(self.hCard, SPC_M2CMD, M2CMD_CARD_WAITREADY)
        self.handle_error()
        print("Card has stopped and is ready.")

    def card_wait_trigger(self):
        """Waits until the first trigger event has been detected by the card. If using a mode with multiple trigger events like Multiple Recording or Gated Sampling there only the first trigger detection will generate an interrupt for this wait command. """
        spcm_dwSetParam_i32(self.hCard, SPC_M2CMD, M2CMD_CARD_WAITTRIGGER)
        self.handle_error()        
        print("Trigger registered.")

    def card_close(self):
        """
        Closes handle to the card.
        """
        if self.hCard is not None:
            spcm_vClose(self.hCard)
            self.hCard = None

    def transfer_single_replay_samples(self, samples):
        """
        Transfers a given array of samples to the memory of the card.

        Parameters:
        - samples: The array of samples to transfer.
        """
        sample_number = len(samples) # number of samples (carefull since the card is 16-bit we need twice as many bytes!)
        
        # Convert the samples array to a ctypes array if it's not already.
        # This depends on the data type of your samples; let's assume they are 16-bit integers.
        sample_array_type = ctypes.c_int16 * sample_number
        samples = sample_array_type(*samples)

        # Check if all samples are 16-bit integers
        if not all(-32768 <= x <= 32768 for x in samples):
            raise ValueError("All samples must be 16-bit integers.")
        
        spcm_dwSetParam_i64(self.hCard, SPC_MEMSIZE, np.int64(np.ceil(sample_number / 4096) * 4096))
        print("Starting the DMA transfer and waiting until data is in board memory ...")
        spcm_dwDefTransfer_i64(self.hCard, SPCM_BUF_DATA, SPCM_DIR_PCTOCARD, 0, byref(samples), 0, sample_number*2)
        spcm_dwSetParam_i32(self.hCard, SPC_M2CMD, M2CMD_DATA_STARTDMA | M2CMD_DATA_WAITDMA)
        print("... data has been transferred to board memory.")

    def set_loops(self, num_loops):
        """
        Sets the number of times the memory is replayed.

        Parameters:
        - num_loops: The number of loops. If set to zero, the generation will run continuously.
        """
        result = spcm_dwSetParam_i64(self.hCard, SPC_LOOPS, num_loops)
        if result != ERR_OK:
            print(f"Failed to set the number of loops: {result}")
            self.handle_error(result)
        else:
            loop_mode = "continuously" if num_loops == 0 else f"{num_loops} times"
            print(f"Memory replay set to run {loop_mode}.")

    def seq_set_memory_segments(self, num_segments):
        """
        Sets the number of memory segments the card should be divided into.

        Parameters:
        - num_segments: The number of segments to divide the memory into. Must be a power of two.

        Note: Changing the number of segments will invalidate previously stored data and sequences.
        """
        # Check if num_segments is a power of two
        if not (num_segments and not(num_segments & (num_segments - 1))):
            raise ValueError("The number of segments must be a power of two.")

        # Set the number of memory segments
        result = spcm_dwSetParam_i32(self.hCard, SPC_SEQMODE_MAXSEGMENTS, num_segments)
        if result != ERR_OK:
            print(f"Failed to set the number of memory segments to {num_segments}.")
            self.handle_error()
        else:
            print(f"The number of memory segments has been set to {num_segments}.")
            print(f"The maximum available memory per segment is: {self.memSize//num_segments} (assuming 1 active channel).")
            print("Warning: All previously stored data and sequences have been invalidated. Please reconfigure your sequence setup.")

    def transfer_sequence_replay_samples(self, segment, samples):
        """
        Transfers a given array of samples to the selected memory segment.

        Parameters:
        - segment: index of the segment to transfer the data to.
        - samples: The array of samples to transfer.
        """

        sample_number = len(samples) # number of samples (carefull since the card is 16-bit we need twice as many bytes!)
        
        # Convert the samples array to a ctypes array if it's not already.
        # This depends on the data type of your samples; let's assume they are 16-bit integers.
        sample_array_type = ctypes.c_int16 * sample_number
        samples = sample_array_type(*samples)

        # Check if all samples are 16-bit integers
        if not all(-32768 <= x <= 32768 for x in samples):
            raise ValueError("All samples must be 16-bit integers.")
        
        # Select correct memory segment
        result = spcm_dwSetParam_i32(self.hCard, SPC_SEQMODE_WRITESEGMENT, segment)
        if result == ERR_OK:
             result = spcm_dwSetParam_i32(self.hCard, SPC_SEQMODE_SEGMENTSIZE,  sample_number)
        if result != ERR_OK:
            print(f"Failed to set the active memory segments to segment number {segment}.")
            self.handle_error()

        print("Starting the DMA transfer and waiting until data is in board memory ...")
        spcm_dwDefTransfer_i64(self.hCard, SPCM_BUF_DATA, SPCM_DIR_PCTOCARD, 0, byref(samples), 0, sample_number*2)
        spcm_dwSetParam_i32(self.hCard, SPC_M2CMD, M2CMD_DATA_STARTDMA | M2CMD_DATA_WAITDMA)
        print("... data has been transferred to board memory.")

    def seq_set_sequence_step(self, step_index, segment_index, next_step, loop_count, end_loop_condition='always', last_step=False):
        """
        Configures a single step in the sequence memory.

        Parameters:
        - step_index: Index of the sequence step to configure (0 to max_steps-1).
        - segment_index: Index of the memory segment associated with this step.
        - next_step: Index of the next step in the sequence.
        - loop_count: Number of times the segment is repeated in this step.
        - end_loop_condition: Condition for moving to the next step ('always', 'on_trigger').
        - last_step: Boolean indicating whether this is the last step in the sequence.
        """
        if step_index < 0 or step_index >= self.seq_max_steps:
            raise ValueError(f"Step index out of range. Must be between 0 and {self.seq_max_steps-1}.")

        # Lower 32 bits: Segment and Next Step Masks
        lower_32 = (segment_index & 0xFFFF) | ((next_step & 0xFFFF) << 16)

        # Upper 32 bits: Loop Mask and Flags
        upper_32 = (loop_count & 0xFFFFF)
        if end_loop_condition == 'on_trigger':
            upper_32 |= SPCSEQ_ENDLOOPONTRIG
        if last_step:
            upper_32 |= SPCSEQ_END

        # Combine the 32-bit parts into a 64-bit value
        sequence_step_value = (upper_32 << 32) | lower_32

        # Write the combined value to the appropriate register
        step_register = SPC_SEQMODE_STEPMEM0 + step_index
        result = spcm_dwSetParam_i64(self.hCard, step_register, sequence_step_value)
        if result != ERR_OK:
            print(f"Failed to set sequence step {step_index}.")
            self.handle_error()  # Assuming handleError is your function for error handling
        else:
            print(f"Sequence step {step_index} configured successfully.")

    def set_segment_size(self, segment_size):
        """
        Sets the length of segments to replay.

        Parameters:
        - segment_size: The length of the segment to replay.
        """
        # Check if segment_size is a power of two
        if not 16 <= segment_size <= self.memSize/2:
            raise ValueError(f"The segment_size must be between 16 and {self.memSize/2 }.")

        # Set the SPC_SEGMENTSIZE register
        result = spcm_dwSetParam_i32(self.hCard, SPC_SEGMENTSIZE, segment_size)
        if result != ERR_OK:
            print(f"Failed to set segment size to {segment_size}.")
            self.handle_error()  # Assuming handleError is your function for error handling
        else:
            print(f"Segment size set to {segment_size} successfully.")

    def fifo_initialize_buffer(self, samples, notify_size):
        """
        Initiallizes FIFO buffer and transfers first set of samples.

        Parameters:
        - samples: The array of samples to transfer.
        - notify_size: The notify size for a new data transfer.
        """
        sample_number = len(samples) # number of samples (carefull since the card is 16-bit we need twice as many bytes!)
        
        # Convert the samples array to a ctypes array if it's not already.
        # This depends on the data type of your samples; let's assume they are 16-bit integers.
        sample_array_type = ctypes.c_int16 * sample_number
        samples = sample_array_type(*samples)

        # Check if all samples are 16-bit integers
        if not all(-32768 <= x <= 32768 for x in samples):
            raise ValueError("All samples must be 16-bit integers.")
        
        print("Starting the DMA transfer and waiting until data is in board memory ...")
        spcm_dwDefTransfer_i64(self.hCard, SPCM_BUF_DATA, SPCM_DIR_PCTOCARD, notify_size, byref(samples), 0, sample_number*2)
        spcm_dwSetParam_i32(self.hCard, SPC_DATA_AVAIL_CARD_LEN, sample_number*2)
        spcm_dwSetParam_i32(self.hCard, SPC_M2CMD, M2CMD_DATA_STARTDMA | M2CMD_DATA_WAITDMA)
        print("... data has been transferred to board memory.")

def generate_single_tone(frequency, num_samples, sample_rate = 1.25e9 ):
    """
    Generates a single tone (sine wave) signal with a specified frequency, number of samples, and sample rate.

    The function calculates a sine wave based on the given frequency and sample rate, then scales the sine wave values
    to fit within the range of a 16-bit integer.

    Parameters:
    - frequency (float): The frequency of the sine wave in Hertz (Hz).
    - num_samples (int): The total number of samples in the generated signal.
    - sample_rate (float, optional): The sample rate in Samples per second (S/s). Defaults to 1.25e9 S/s.

    Returns:
    - numpy.ndarray: An array of int16 values representing the generated sine wave signal.
    """
    duration = num_samples/sample_rate  # Duration to cover one cycle of the sine wave, in seconds

    # Calculate the number of samples needed for one cycle
    print(f"Number of samples: {num_samples}")
    # Generate time values
    t = np.linspace(0, duration, num_samples, endpoint=False)
    
    return np.int16(np.sin(2 * np.pi * frequency * t) * 32767)

def generate_multi_tone(frequencies, amplitudes, phases, num_samples, sample_rate=1.25e9, print_crest_factor=False):
    """
    Generates a signal that is the sum of multiple sine waves, with normalization to prevent overflow.

    Parameters:
    - frequencies: A list of frequencies for the sine waves.
    - amplitudes: A list of amplitudes for the sine waves. Must be the same length as frequencies.
    - phases: A list of phases for the sine waves. Must be the same length as frequencies.
    - num_samples: The total number of samples in the generated signal.
    - sample_rate: The sample rate in Hz.

    Returns:
    - An array containing the generated signal, normalized and cast to int16.
    """

    # Duration to cover the desired number of samples
    duration = num_samples / sample_rate

    # Generate time values
    t = np.linspace(0, duration, num_samples, endpoint=False)

    # Initialize the signal with zeros
    signal = np.zeros(num_samples)

    # Accumulate sine waves for each frequency and amplitude pair
    for frequency, amplitude, phase in zip(frequencies, amplitudes, phases):
        signal += amplitude * np.sin(2 * np.pi * frequency * t + phase)

    # Normalize the signal to the range [-32767, 32767] to prevent overflow when casting to int16
    # Find the peak value
    peak_value = np.abs(signal).max()
    if peak_value > 0:
        # Normalize signal
        normalization_factor = 32767 / peak_value
        signal = signal * normalization_factor

    if print_crest_factor:
        crest_factor = 32767 / np.sqrt(np.mean(signal**2))
        print(f"Crest facor of signal: {crest_factor:.3f}")

    return np.int16(signal)
