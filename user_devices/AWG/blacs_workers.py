from blacs.device_base_class import Worker

# Define the Spectrum Instrument AWG worker class
class SpectrumAWGWorker(Worker):
    def init(self):
        # Connect to the AWG
        self.awg_connection = lascar.awg.Connect()

    def shutdown(self):
        # Disconnect from the AWG
        self.awg_connection.disconnect()

    def program_manual(self, values):
        # Retrieve the desired settings from the values dictionary
        enable_output = values['Output Enabled']
        amplitude = values['Amplitude']
        frequency = values['Frequency']
        waveform_data = values['Waveform Data']

        # Set the output enable state
        self.awg_connection.setOutput(1, enable_output)

        # Set the amplitude and frequency
        self.awg_connection.setAmplitude(1, amplitude)
        self.awg_connection.setFrequency(1, frequency)

        # Create a waveform and upload it to the AWG
        waveform_id = 1  # ID of the waveform to create
        self.awg_connection.createWaveform(waveform_id, waveform_data)
        self.awg_connection.selectWaveform(1, waveform_id)

        # Start or stop the AWG output based on the output enable state
        if enable_output:
            self.awg_connection.startOutput(1)
        else:
            self.awg_connection.stopOutput(1)


