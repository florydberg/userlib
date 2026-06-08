from blacs.tab_base_classes import Worker
import lascar

from blacs.tab_base_classes import define_state, MODE_MANUAL
from blacs.device_base_class import DeviceTab

from qtutils import UiLoader, inmain_decorator
import qtutils.icons
from qtutils.qt import QtWidgets, QtGui, QtCore

# set number of channels
MAX_NUM_CHANNELS = 4

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


# Define the Spectrum Instrument AWG TAB class
class SpectrumAWGTab(DeviceTab):

    def initialise_GUI(self):

        # Capabilities
        self.base_units = {'freq': 'MHz', 'amp': 'dBm', 'phase': 'Degrees'}
        self.base_min = {'freq': MIN_RF_FREQ, 'amp': MIN_RF_AMP, 'phase': MIN_RF_PHASE}
        self.base_max = {'freq': MAX_RF_FREQ, 'amp': MAX_RF_AMP, 'phase': MAX_RF_PHASE}
        self.base_step = {'freq': 1.0, 'amp': 1.0, 'phase': 1.0}
        self.base_decimals = {'freq': 6, 'amp': 2, 'phase': 3}  # TODO: find out what the phase precision is!
        self.num_DDS = MAX_NUM_CHANNELS



        layout = self.get_tab_layout()
        ui_filepath = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), 'blacs_tab.ui'
        )
    
        attributes_ui_filepath = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), 'attributes_dialog.ui'
        )
        
        # Create the controls for the AWG
        self.create_connection_tab()
        self.create_device_attributes()
        self.create_worker_tab(classname='__main__.SpectrumAWGWorker')

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
        self.setTabLayout(
            [
                {'tab': 'Control', 'widget': self.control_widget},
                {'tab': 'Monitor', 'widget': self.monitor_widget},
            ]
        )
    
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