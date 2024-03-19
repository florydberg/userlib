#####################################################################
# AWG device by Andrea Fantini
# created 5/7/2023
#####################################################################
import sys
from labscript_utils import dedent
from labscript import Device, TriggerableDevice, set_passed_properties
import numpy as np
import labscript_utils.h5_lock
import h5py
from labscript_devices import runviewer_parser
from labscript import *
import lascar
from user_devices.AWG.register_classes import register_classes

# To be called in connection_table 
# awg_connection = lascar.awg.Connect()
# awg = SpectrumAWG('awg', parent_device=None, connection=connection)
####################################################

# load registers for easier access
from user_devices.AWG.py_header.regs import *

# load registers for easier access
from user_devices.AWG.py_header.spcerr import *

# Define the AWG device
class SpectrumAWG(Device):
    description = 'Spectrum Instrument AWG'

    def __init__(self, name, parent_device, connection):
       
        # Register the device with labscript
        # self.supports_smart_programming(True)
        # self.BLACS_connection = self.parent_device.BLACS_connection
        
        Device.__init__(self, name, parent_device, connection)

    def program_manual(self, front_panel_values):
        # Retrieve the desired settings from front_panel_values dictionary
        enable_output = front_panel_values['Output Enabled']
        amplitude = front_panel_values['Amplitude']
        frequency = front_panel_values['Frequency']
        waveform_data = front_panel_values['Waveform Data']

        # Set the output enable state
        self.connection.setOutput(1, enable_output)

        # Set the amplitude and frequency
        self.connection.setAmplitude(1, amplitude)
        self.connection.setFrequency(1, frequency)

        # Create a waveform and upload it to the AWG
        waveform_id = 1  # ID of the waveform to create
        self.connection.createWaveform(waveform_id, waveform_data)
        self.connection.selectWaveform(1, waveform_id)

        # Start or stop the AWG output based on the output enable state
        if enable_output:
            self.connection.startOutput(1)
        else:
            self.connection.stopOutput(1)


