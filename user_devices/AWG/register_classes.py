from labscript_devices import labscript_device, BLACS_tab, BLACS_worker, runviewer_parser
from labscript import *
from labscript_devices import register_classes


# Define the Spectrum Instrument AWG class
class SpectrumAWG(Device):
    description = 'Spectrum Instrument AWG'
    # allowed_children = [Waveform]
    generation = 2  # Set the generation to 2 for BLACS support

    @staticmethod
    def worker_class():
        return SpectrumAWGWorker

# # Define the Spectrum Instrument AWG worker class
# class SpectrumAWGWorker(BLACS_worker):
#     def program_manual(self, values):
#         # Retrieve the desired settings from the values dictionary
#         enable_output = values['Output Enabled']
#         amplitude = values['Amplitude']
#         frequency = values['Frequency']
#         waveform_data = values['Waveform Data']

#         # Set the output enable state
#         self.connection.setOutput(1, enable_output)

#         # Set the amplitude and frequency
#         self.connection.setAmplitude(1, amplitude)
#         self.connection.setFrequency(1, frequency)

#         # Create a waveform and upload it to the AWG
#         waveform_id = 1  # ID of the waveform to create
#         self.connection.createWaveform(waveform_id, waveform_data)
#         self.connection.selectWaveform(1, waveform_id)

#         # Start or stop the AWG output based on the output enable state
#         if enable_output:
#             self.connection.startOutput(1)
#         else:
#             self.connection.stopOutput(1)

# Register the classes
register_classes(
    SpectrumAWG,
    runviewer_parser=runviewer_parser,
    BLACS_tab=BLACS_tab,
    # BLACS_worker=BLACS_worker,
)