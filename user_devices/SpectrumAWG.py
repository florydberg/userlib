#####################################################################
# AWG device by Andrea Fantini
# created 5/7/2023
#####################################################################
import sys
import lascar
import numpy as np
import labscript_utils.h5_lock
import h5py

from labscript import *
from labscript_utils import dedent

from labscript_devices import runviewer_parser, labscript_device, BLACS_tab, BLACS_worker
from blacs.tab_base_classes import define_state, MODE_MANUAL
from blacs.device_base_class import DeviceTab
from blacs.device_base_class import Worker

from qtutils import UiLoader, inmain_decorator
from qtutils.qt import QtWidgets, QtGui, QtCore
import qtutils.icons

from user_devices.AWG.register_classes import register_classes
from user_devices.AWG.py_header.regs import *
from user_devices.AWG.py_header.spcerr import *
from user_devices.AWG.AWG_sdk.spcm_tools import *

import os
import platform
from ctypes import *

# load registers for easier access
from py_header.regs import *

# load registers for easier access
from py_header.spcerr import *

# To be called in connection_table #######################################
# awg_connection = lascar.awg.Connect()
# awg = SpectrumAWG('awg', parent_device=None, connection=connection)
##########################################################################

# pointers (do not set False) (from pyspcm)
if True:
    from user_devices.AWG.AWG_sdk.pyspcm import *

    SPCM_DIR_PCTOCARD = 0
    SPCM_DIR_CARDTOPC = 1

    SPCM_BUF_DATA      = 1000 # main data buffer for acquired or generated samples
    SPCM_BUF_ABA       = 2000 # buffer for ABA data, holds the A-DATA (slow samples)
    SPCM_BUF_TIMESTAMP = 3000 # buffer for timestamps

    # define pointer aliases
    int8  = c_int8
    int16 = c_int16
    int32 = c_int32
    int64 = c_int64

    ptr8  = POINTER (int8)
    ptr16 = POINTER (int16)
    ptr32 = POINTER (int32)
    ptr64 = POINTER (int64)

    uint8  = c_uint8
    uint16 = c_uint16
    uint32 = c_uint32
    uint64 = c_uint64

    uptr8  = POINTER (uint8)
    uptr16 = POINTER (uint16)
    uptr32 = POINTER (uint32)
    uptr64 = POINTER (uint64)


# values (do not set False)
if True:
    log_level = [logging.CRITICAL, logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG, logging.NOTSET][2]

    # set number of channels
    MAX_NUM_CHANNELS = 2

    # min/max RF frequency in MHz
    MIN_RF_FREQ     = 20.0
    MAX_RF_FREQ     = 200.0
    DEFAULT_RF_FREQ = MIN_RF_FREQ

    # min/max RF amplitudes in dBm
    MIN_RF_AMP      = -50.0
    MAX_RF_AMP      = 33.0

    # min/max RF phase in degree
    MIN_RF_PHASE    = 0
    MAX_RF_PHASE    = 360

    # measured trigger delay in table in seconds. there is a jitter of 5us.
    TABLE_MIN_TRIGGER_DELAY = 3.5e-6
    TABLE_MAX_TRIGGER_DELAY = 8.5e-6

    # trigger delay for switching RF on/off when not in table mode.
    # this maximum value given is the specified value. the minimum value was measured.
    # no jitter seen but could be different from device to device.
    NO_TABLE_MIN_TRIGGER_DELAY = 25e-9
    NO_TABLE_MAX_TRIGGER_DELAY = 40e-9

    # this applies only for Table mode
    # clock resolution and limit calculated from MAX_BUS_RATE.
    # MAX_BUS_RATE is the maximum data output rate in Hz on the bus. individual devices can give a lower rate but not higher.
    # times are rounded to nearest integer multiple of clock_resolution in quantise_to_pseudoclock in labscript.py.
    # time deltas dt are checked vs. dt < 1/clock_line.clock_limit in collect_change_times in labscript.py.
    # we add epsilon(MAX_TIME) to clock_limit to avoid that small numberical errors cause problems.
    def epsilon(number):
        """
        returns smallest epsilon for which number + epsilon != number.
        sys.float_info.epsilon = epsilon(1.0)
        """
        e = number
        while(number + e != number):
            e /= 2
        return 2*e
    # limits in TABLE mode
    TABLE_CLOCK_RESOLUTION = 5e-6
    TABLE_MAX_BUS_RATE     = 1/TABLE_CLOCK_RESOLUTION
    TABLE_MAX_TIME         = ((2**32)-1)*TABLE_CLOCK_RESOLUTION # TODO: not clear what is largest time? maybe only 16bits?
    TABLE_CLOCK_LIMIT      = 1.0/(TABLE_CLOCK_RESOLUTION - 2*epsilon(TABLE_MAX_TIME))
    # limits when not in TABLE mode depdns on actual FPGA board clock resolution
    NO_TABLE_CLOCK_RESOLUTION = NO_TABLE_MAX_TRIGGER_DELAY
    NO_TABLE_MAX_BUS_RATE     = 1/NO_TABLE_CLOCK_RESOLUTION
    def get_clock_limit(clock_resolution):
        return 1.0/(NO_TABLE_CLOCK_RESOLUTION - 2*epsilon(((2**32)-1)*clock_resolution))
    #print('Moglabs QFR: maximum bus rate %.3f MHz gives resolution %.3f ns and max time %.3f s (clock limit = bus rate + %.3f Hz)' % (MAX_BUS_RATE/1e6, CLOCK_RESOLUTION*1e9, MAX_TIME, CLOCK_LIMIT - MAX_BUS_RATE))

    # table options passed to worker
    FLAG_TABE_MODE          = 1
    FLAG_TRIGGER_EACH_STEP  = 2


class AWG_DDS(IntermediateDevice):
    description = "AWG DDS"
    allowed_children = [DDS]
    generation = 1

    def __init__(self, name, parent_device, connection, table_mode=True, **kwargs):
        IntermediateDevice.__init__(self, name, parent_device, connection, **kwargs)

        # trigger delay and resolution depend if we are in table mode or not
        # in non-table mode we take limits of parent board
        if self.table_mode:
            self.trigger_delay = TABLE_MAX_TRIGGER_DELAY
            self.bus_rate      = TABLE_MAX_BUS_RATE
            self.clock_limit   = TABLE_CLOCK_LIMIT
            self.clock_resolution = TABLE_CLOCK_RESOLUTION
        else:
            self.trigger_delay = NO_TABLE_MAX_TRIGGER_DELAY
            self.bus_rate      = NO_TABLE_MAX_BUS_RATE
            #self.clock_limit   = get_clock_limit(parent_board.clock_resolution)
            #self.clock_resolution = parent_board.clock_resolution
            self.clock_limit   = get_clock_limit(1e-6)
            self.clock_resolution = 1e-6

        # create pseudoclock
        # Pseudoclock is initialized with the parent_device clock limit/resolution which is NOT what we want.
        # we want limit/resolution of this device. the paren_device will set its limit/resolution to the fastest clock.
        # we call add_device later when chain of devices is created othwise lists of child_devices are empty
        self.pseudoclock = Pseudoclock(name=name+'_ps', pseudoclock_device=parent_device, connection='ps%i'%digital_gate['connection'], call_parents_add_device=False)
        self.pseudoclock.clock_limit = self.clock_limit
        self.pseudoclock.clock_resolution = self.clock_resolution

        # create clockline
        self.clockline = ClockLine(name=name+'_cl', pseudoclock=self.pseudoclock, connection='cl%i'%digital_gate['connection'])

        # init class. this will call parent_device.add_device
        IntermediateDevice.__init__(self, 'QRF_%s'%name, parent_device=self.clockline)

        # create new DDS. self.DDS.gate contains new DigitalOutput used as trigger
        self.DDS = DDSQuantity(name, parent_device=self, connection=connection, digital_gate=digital_gate)

        # set default frequency in MHz
        self.DDS.frequency.default_value = DEFAULT_RF_FREQ

        # notify MOGLabs_QRF of new pseudoclock. this will adapt the clock_limt and clock_resolution to fastest clock
        parent_device.add_device(self.pseudoclock)


# Define the AWG device
class SpectrumAWG(PseudoclockDevice):
    description = 'Spectrum Instrument AWG'

    allowed_children = [Pseudoclock]

    
    clock_limit = get_clock_limit(1e-6)
    min_clock_limit=clock_limit
    clock_resolution = 1e-6
    trigger_delay = 1e-6
    trigger_minimum_duration = 5e-6

    @set_passed_properties(
        property_names={'connection_table_properties': ['addr', 'port', 'worker_args']}
    )

    def __init__(self, name, parent_device,  connection, addr=None, port=7802,  worker_args=None):
        self.BLACS_connection = '%s,%s' % (addr, str(port))

        self.name = name
        self.parent_device = parent_device # will be replaced with digital channel of fastest QRF_DDS
        self.parent_board  = parent_device
       
        # Register the device with labscript
        # self.supports_smart_programming(True)
        # self.BLACS_connection = self.parent_device.BLACS_connection
        
        PseudoclockDevice.__init__(self, name, parent_device, connection)


@BLACS_tab
# Define the Spectrum Instrument AWG TAB class
class SpectrumAWG_Tab(DeviceTab):

    def initialise_GUI(self):

        # Capabilities
        self.base_units = {'freq': 'MHz', 'amp': 'dBm', 'phase': 'Degrees'}
        self.base_min = {'freq': MIN_RF_FREQ, 'amp': MIN_RF_AMP, 'phase': MIN_RF_PHASE}
        self.base_max = {'freq': MAX_RF_FREQ, 'amp': MAX_RF_AMP, 'phase': MAX_RF_PHASE}
        self.base_step = {'freq': 1.0, 'amp': 1.0, 'phase': 1.0}
        self.base_decimals = {'freq': 6, 'amp': 2, 'phase': 3}  # TODO: find out what the phase precision is!
        self.num_DDS = MAX_NUM_CHANNELS

        connection_object = self.settings['connection_table'].find_by_name(self.device_name)
        connection_table_properties = connection_object.properties

        self.addr = connection_table_properties['addr']
        self.port = connection_table_properties['port']
        self.worker_args = connection_table_properties['worker_args']

        # Create and set the primary worker
        self.create_worker("main_worker", SpectrumAWG_Worker, {'addr': self.addr, 'port': self.port, 'worker_args': self.worker_args})
        self.primary_worker = "main_worker"

        layout = self.get_tab_layout()
        ui_filepath = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), 'blacs_tab.ui'
        )
    
        attributes_ui_filepath = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), 'attributes_dialog.ui'
        )
        
        ## Create the controls for the AWG
        # self.create_connection_tab()
        # self.create_device_attributes()
        # self.create_worker_tab(classname='__main__.SpectrumAWGWorker')

        # Create the worker for the Spectrum AWG
        self.create_worker("main", "SpectrumAWGWorker")

        # Create the control and monitor widgets
        self.control_widget = QtWidgets.QWidget()
        self.monitor_widget = QtWidgets.QWidget()

        # Add widgets and layout for the control tab
        control_layout = QtWidgets.QVBoxLayout(self.control_widget)
        control_layout.addWidget(QtWidgets.QLabel("Control Tab Content"))
        # Add more widgets or customize the control tab layout as needed

        # Add widgets and layout for the monitor tab
        monitor_layout = QtWidgets.QVBoxLayout(self.monitor_widget)
        monitor_layout.addWidget(QtWidgets.QLabel("Monitor Tab Content"))
        # Add more widgets or customize the monitor tab layout as needed

        # Set the created widgets as the tab contents
        # self.setTabLayout(
        #     [
        #         {'tab': 'Control', 'widget': self.control_widget},
        #         {'tab': 'Monitor', 'widget': self.monitor_widget},
        #     ]
        # )
    
    def run_shot(t):
        # Set the desired settings for the AWG
        self.set_property('Output Enabled', True)
        self.set_property('Amplitude', 2.5)
        self.set_property('Frequency', 1000)
        self.set_property('Waveform Data', [0, 1, 0, -1])

        # Trigger the AWG output for the desired duration
        t.awg_trigger(awg, duration=5)

    def get_selected_device_worker_class(self):
        return SpectrumAWGWorker

    def get_default_workers(self):
        return {"main": "SpectrumAWGWorker"}
    
    @define_state(MODE_MANUAL, queue_state_indefinitely=True, delete_stale_states=True)
    def update_attributes(self):
        attributes_text = yield (
            self.queue_work(
                self.primary_worker,
                'get_attributes_as_text',
                self.attributes_dialog.comboBox.currentText(),
            )
        )
        self.attributes_dialog.plainTextEdit.setPlainText(attributes_text)

    def restart(self, *args, **kwargs):
        # Must manually stop the receiving server upon tab restart, otherwise it does
        # not get cleaned up:
        self.image_receiver.shutdown()
        return DeviceTab.restart(self, *args, **kwargs)
    

# Define the Spectrum Instrument AWG worker class
class SpectrumAWG_Worker(Worker):
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

    def transition_to_buffered(self, device_name, h5file, initial_values, fresh):
        # try to reconnect. return on failure.
        if (self.dev is None) and (not self.reconnect('check_remote_values')):

            if True:
                print('%s cannot connect. test reading hdf5 file....' % (device_name))
                with h5py.File(h5file, 'r') as hdf5_file:
                    group = hdf5_file['/devices/' + device_name]
                    for i in range(MAX_NUM_CHANNELS):
                        table_name = 'TABLE_OPT%i'%i
                        if table_name in group:
                            flags = group[table_name][:][0]
                            print('%s / channel %i options:' % (device_name, i), flags)
                            table_mode        = (flags & FLAG_TABE_MODE        ) == FLAG_TABE_MODE
                            trigger_each_step = (flags & FLAG_TRIGGER_EACH_STEP) == FLAG_TRIGGER_EACH_STEP
                            print('table mode %s, trigger each step %s' % (table_mode, trigger_each_step))
                        table_name = 'TABLE_DATA%i'%i
                        if table_name in group:
                            table_data = group[table_name][:] 
                            print('%s / channel %i data:' % (device_name, i), table_data)
