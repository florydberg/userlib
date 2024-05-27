from labscript import Device, Output, Trigger, LabscriptError, config, set_passed_properties
import numpy as np

class AWGOutput(Output):
    description = 'Arbitray Waveform Output'

    def __init__(self, name, parent_device, connection, trigger_device, trigger_connection, channel_amplitude, **kwargs):
        """ Create Output channel for AWG.
        
        Parameters
        ----------
        name : str
            Name for device.
        parent_device : 
            Instance of AWG
        connection : str
            Number of channel.
        trigger_device : 
            Instance of device (InternediateDevice with digital output) that triggers the channel.
        trigger_connection : str
            Channel of Trigger in trigger_device
        channel_amplitude : int
            Maximal (positive and negative) amplitude of channel output in mV.
        """
        parent_device.set_property(f"channel_amplitude_{connection}", channel_amplitude, "connection_table_properties")
        super().__init__(name, parent_device, connection, limits=None, unit_conversion_class=None, unit_conversion_parameters=None, default_value=None, **kwargs)
        if isinstance(trigger_device, Trigger):
            if "rising" != trigger_device.trigger_edge_type:
                raise LabscriptError('Trigger edge type for %s is \'%s\', ' % (name, self.trigger_edge_type) + 
                                      'but existing Trigger object %s ' % trigger_device.name +
                                      'has edge type \'%s\'' % trigger_device.trigger_edge_type)
            self.trigger_device = trigger_device
        elif trigger_device is not None:
            # Instantiate a trigger object to be our parent:
            self.trigger_device = Trigger(name+"_trigger", trigger_device, trigger_connection, trigger_edge_type="rising")

    def add_instruction(self, time, instruction, units=None):
        if time in self.instructions:
            raise LabscriptError(f"Spectrum AWG aleady has another instruction programmed at t={time}!")
        
        if self.trigger_device is not None:
            self.trigger_device.trigger(time,duration=50e-6)

        return super().add_instruction(time, instruction, units)

    def calculate_num_samples(self, sample_duration):
        # The sample size has to be multiples of 4096, so we have to quantize to that value.
        # With the (maximal) sample rate of 1.25GHz, this means the sample duration has minimal
        # steps of 3.2769µs.
        num_samples = np.round(sample_duration*self.parent_device.sample_rate/4096)*4096
        return num_samples

    def generate_single_tone(self, t, sample_duration, frequency, label=None):
        """
        Parameters
        ----------
        t : float
            Time when stream starts, in seconds.
        sample_duration : float
            Duration of sample (that gets repeated), in seconds.
        frequency : float
            in Hz.
        label : str, optional
            Description of the instruction
        """
        num_samples = self.calculate_num_samples(sample_duration)

        # Check frequency resolution
        fundamental_frequency = np.round(1/sample_duration)
        if frequency<fundamental_frequency:
            raise LabscriptError(f"Freqeuncy of '{self.name}' at t={t} is smaller than the resolution ({fundamental_frequency:i}), change frequency or sample size/duration.")

        self.add_instruction(t,(num_samples,frequency,label))

    def generate_multiple_tones(self, t, sample_duration, frequencies, amplitudes=None, phases=None, label=None):
        """
        Parameters
        ----------
        t : float
            Time.
        frequencies : 
            Iterable of frequencies for each tone
        amplitude : (optional)
            Relative amplitude of each tone. If None, all have the same amplitude.
        phase : (optional)
            Phase for each tone. If None, all tones of zero (the same) phase.
        label : str, optional
            Description of the instruction
        """
        num_samples = self.calculate_num_samples(sample_duration)
        frequencies = np.array(frequencies)
        if amplitudes is None:
            amplitudes = np.ones(len(frequencies))
        if phases is None:
            phases = np.zeros(len(frequencies))
            # TODO: for equally spaced frequencies using 
            # phases = np.pi*np.arange(len(frequencies))**2/len(frequencies)
            # are good values.

        # Check frequency resolution
        freq_sorted = np.sort(frequencies)
        fundamental_frequency = np.round(1/sample_duration)
        if np.any(frequencies<fundamental_frequency) or np.any((freq_sorted[1:]-freq_sorted[:-1])<fundamental_frequency):
            raise LabscriptError(f"Freqeuncy or difference of '{self.name}' at t={t} is smaller than the resolution ({fundamental_frequency:.0f}Hz), change frequency or sample size/duration.")

        if not len(frequencies)==len(amplitudes)==len(phases):
            raise LabscriptError(f"Instruction for '{self.name}' at t={t} must have a frequency, amplitude and phase for all tones or none.")
        
        self.add_instruction(t, (num_samples,*frequencies,*amplitudes, *phases, label))

    def do_checks(self):
        for t,instruction in self.instructions.items():
            if instruction[0]>self.parent_device.max_sample_size:
                raise LabscriptError(f"Instruction for '{self.name}' at t={t} has too many samples (num_samples={instruction[0]:.0f}).")
            


class SpectrumAWG(Device):
    description = "Spectrum Instrumentation Arbitray Waveform Generator"
    allowed_children = [AWGOutput]

    @set_passed_properties(
        property_names={"connection_table_properties": ["device_path","timeout","external_clock_rate","sample_rate","memory_segments"],
                        "device_properties": []                
        }
        )
    def __init__(self, name, device_path, sample_rate, external_clock_rate=None, timeout=5000, channel_mode="seq", memory_segments=2**16, **kwargs):
        """ Create SpectrumAWG instance.
        
        Parameters
        ----------
        name : str
            Name for device.
        device_path : str
            Path to find the hardware for the spcm driver (e.g. '/dev/spcm0').
        timeout : int
            Timeout for opterations in BLACS worker, in milliseconds.
        external_clock_rate : int
            Frequency of the external clock (ClkIn) in Hz. If None, the card uses the internal clock.
        channel_mode : str
            Sets the output mode of the AWG channel between sequence ('seq') and streaming ('fifo').
            TODO: implemet fifo mode
        memory_segments : int
            In sequence mode how many different segments can be stored in memory.
        """
        super().__init__(name, parent_device=None, connection="None", **kwargs)
        self.BLACS_connection = device_path
        self.channel_mode = channel_mode
        self.sample_rate = sample_rate
        self.memory_segments = memory_segments

        # Calculate maximal sample size
        internal_memory = 2**32 # 4GB
        self.max_sample_size = internal_memory//2//memory_segments # TODO: according to the messages in the worker we don't need the factor 2 here

    def do_checks(self):
        if len(self.child_devices)>1:
            raise NotImplementedError("This code can just handle 1 output channel for now.")

    def generate_code(self, hdf5_file):
        group = hdf5_file.require_group(f"devices/{self.name}")

        self.do_checks()

        for output in self.child_devices:
            output.do_checks()

            change_times = output.get_change_times()
            group.require_group(output.connection)
            group[output.connection].require_group("labels")

            for i,t in enumerate(np.sort(change_times)):
                group[output.connection].attrs[str(i)] = output.instructions[t][:-1]
                if output.instructions[t][-1] is not None:
                    group[output.connection]["labels"].attrs[str(i)] = output.instructions[t][-1]

        



if __name__=="__main__":
    from labscript import start
    import h5py

    # Create hdf5 file for testing
    with h5py.File("user_devices/SpectrumAWG/testing/labscript_devices.h5","w") as hdf5_file:
        hdf5_file.require_group("devices")
        SpectrumAWG("TestAWG","/dev/spcm0",timeout=5000,sample_rate=1250e6)
        AWGOutput("Tweezers", TestAWG, "0", None, None, 100)

        start()
        Tweezers.generate_single_tone(1,1e-3,10e6)
        Tweezers.generate_single_tone(0,1e-3,20e6)
        Tweezers.generate_multiple_tones(10,1e-3,[1e6,2e6,3e6])

        TestAWG.generate_code(hdf5_file)

        stop(11)
 