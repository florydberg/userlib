import time
from blacs.device_base_class import DeviceTab
from blacs.tab_base_classes import Worker
import lascar

# Define the Spectrum Instrument AWG TAB class
class SpectrumAWGTab(DeviceTab):
    def initialise_GUI(self):
        # Create the controls for the AWG
        self.create_connection_tab()
        self.create_device_attributes()
        self.create_worker_tab(classname='__main__.SpectrumAWGWorker')

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

# Create a test script to run the AWG in BLACS
def test_awg():
    # Create a connection to the AWG
    awg_connection = lascar.awg.Connect()

    # Configure the AWG settings
    awg_connection.setOutput(1, True)  # Enable output on channel 1
    awg_connection.setAmplitude(1, 2.5)  # Set amplitude to 2.5 Vpp on channel 1
    awg_connection.setFrequency(1, 1000)  # Set frequency to 1 kHz on channel 1

    # Create a waveform and upload it to the AWG
    waveform_data = [0, 1, 0, -1]  # Example waveform (replace with your desired waveform)
    waveform_id = 1  # ID of the waveform to create
    awg_connection.createWaveform(waveform_id, waveform_data)  # Create waveform with ID 1
    awg_connection.selectWaveform(1, waveform_id)  # Select waveform 1 for channel 1

    # Start the AWG output
    awg_connection.startOutput(1)

    # Wait for a few seconds
    time.sleep(5)

    # Stop the AWG output
    awg_connection.stopOutput(1)

    # Disconnect from the AWG
    awg_connection.disconnect()

# Run the test script
if __name__ == '__main__':
    test_awg()