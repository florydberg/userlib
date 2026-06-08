from blacs.device_base_class import DeviceTab, MODE_MANUAL, MODE_BUFFERED, define_state
from qtutils.qt import QtGui, QtWidgets
from qtutils import UiLoader
import os
import pyqtgraph as pg
from pyqtgraph import PlotWidget
import numpy as np
import re
from PyQt5.QtWidgets import QWidget, QGridLayout, QCheckBox


DDS_mode=1

def parse_frequency_input(text):
    text = text.replace(" ", "")

    # Caso linspace
    if text.startswith("linspace"):
        match = re.match(r"linspace\((.*?),(.*?),(.*?)\)", text)
        if match:
            start, stop, num = map(float, match.groups())
            return list(np.linspace(start, stop, int(num)))

    # Caso lista separata da virgole
    if "," in text:
        return [float(x) for x in text.split(",")]

    # Caso singolo valore
    return [float(text)]


class SpectrumAWGTab(DeviceTab):
    def initialise_GUI(self):
        connection = self.settings['connection_table'].find_by_name(self.device_name)
        props = connection.properties

        self.create_worker(
            'main_worker',
            'user_devices.SpectrumAWG.blacs_workers.SpectrumAWGWorker',
            props,
        )
        self.primary_worker = 'main_worker'

        # Set the capabilities of this device
        self.supports_remote_value_check(False)
        self.supports_smart_programming(True)
        self.manual_active = False

        # Create UI
        self.ui = UiLoader().load(os.path.join(os.path.dirname(os.path.realpath(__file__)),"./blacs_widget.ui"))
        self.start_icon = QtGui.QIcon(':/qtutils/fugue/control')
        self.stop_icon = QtGui.QIcon(':/qtutils/fugue/control-stop-square')

        self.ui.comboBox_triggerSource.currentIndexChanged.connect(lambda: self.update_trigger_source())

        self.ui.comboBox_X0.currentIndexChanged.connect(lambda: self.update_Multi_IO('X0'))
        self.ui.comboBox_X1.currentIndexChanged.connect(lambda: self.update_Multi_IO('X1'))
        self.ui.comboBox_X2.currentIndexChanged.connect(lambda: self.update_Multi_IO('X2'))

        self.auto_place_widgets(("Manual settings",{"AWG":self.ui}))

        # Memory
        # self.ui.used_memory.setMaximum(props["memory_segments"])
        # self.ui.pushButton_MemoryReplay.setIcon(self.start_icon)
        
        # self.ui.pushButton_reset.setIcon(QtGui.QIcon(':/qtutils/fugue/broom'))
        # self.ui.pushButton_reset.clicked.connect(lambda: self.reset_card())
        
        # self.ui.pushButton_MemoryReplay.clicked.connect(lambda: self.manual_memory_replay())

        ## DDS static widget
        self.static_ui = UiLoader().load(os.path.join(os.path.dirname(os.path.realpath(__file__)),"./DDSstatic_blacs_widget.ui"))

        self.static_ui.pushButton_SingleTone.setIcon(self.start_icon)

        if not DDS_mode:
            self.static_ui.pushButton_SingleTone.clicked.connect(lambda: self.manual_multi_tone())
            self.static_ui.spinBox_NumSamples.valueChanged.connect(lambda: self.update_number_of_samples())
            self.static_ui.spinBox_sampleRate.valueChanged.connect(lambda: self.update_sample_rate())
        else:
            self.static_ui.pushButton_SingleTone.clicked.connect(lambda: self.dds_static())
            self.static_ui.spinBox_sampleRate.setEnabled(False)
            self.static_ui.spinBox_NumSamples.setEnabled(False)

        self.auto_place_widgets(("DDS static",{"DDS_static":self.static_ui}))
        # self.layout.addWidget(self.static_ui, alignment=QtCore.Qt.AlignTop)

        ## DDS slope widget
        self.slope_ui = UiLoader().load(os.path.join(os.path.dirname(os.path.realpath(__file__)),"./DDSslope_blacs_widget.ui"))

        self.slope_ui.pushButton_Slope.setIcon(self.start_icon)
        self.slope_ui.pushButton_Slope.clicked.connect(lambda: self.dds_slope())

        self.auto_place_widgets(("DDS slope", {"DDS_slope": self.slope_ui}))

    @define_state(MODE_MANUAL,False)
    def update_Multi_IO(self, connection):
        """
        Update the Multi IO connection based on the selected value in the combo box.
        """
        print('yes')
        value = self.ui.findChild(QtWidgets.QComboBox, f"comboBox_{connection}").currentText()
        yield(self.queue_work(self._primary_worker, 'change_Multi_IO', connection, value)) 
     
    def get_front_panel_values(self):
        return self._final_values

    @define_state(MODE_MANUAL,False)
    def update_trigger_source(self):
        source=self.ui.comboBox_triggerSource.currentText()
        yield(self.queue_work(self._primary_worker, 'change_triggerSource', source))

    @define_state(MODE_MANUAL,False)
    def update_sample_rate(self):
        sample_rate=self.static_ui.spinBox_sampleRate.value()
        yield(self.queue_work(self._primary_worker, 'change_sampleRate', sample_rate))
    
    @define_state(MODE_MANUAL,False)
    def update_number_of_samples(self):
        num_samples=2**self.static_ui.spinBox_NumSamples.value()
        yield(self.queue_work(self._primary_worker, 'change_sampleNum', num_samples))
    
    @define_state(MODE_BUFFERED,False)
    def transition_to_manual(self,notify_queue,program=False):

        # self.ui.comboBox_memory.clear()
        for memory_index,instruction in self._final_values.items():
            print(self._final_values.items())
            # self.ui.comboBox_memory.addItem(f"{memory_index} {instruction}")
        # self.ui.comboBox_memory.view().setMinimumWidth(self.ui.comboBox_memory.view().sizeHintForColumn(0)+30)

        super().transition_to_manual(notify_queue,program=False)
        # self.ui.used_memory.setValue(len(self._final_values))

    @define_state(MODE_MANUAL,False)
    def manual_single_tone(self):
        if not self.manual_active:
            frequency = self.static_ui.doubleSpinBox_frequency.value()
            self.static_ui.pushButton_SingleTone.setIcon(self.stop_icon)
            self.slope_ui.pushButton_Slope.setIcon(self.stop_icon)
            # self.static_ui.pushButton_MemoryReplay.setEnabled(False)
            self.manual_active = True
            yield(self.queue_work(self._primary_worker,'program_manual',frequency))
        else:
            self.static_ui.pushButton_SingleTone.setIcon(self.start_icon)
            # self.static_ui.pushButton_MemoryReplay.setEnabled(True)
            self.manual_active = False
            yield(self.queue_work(self._primary_worker,'program_manual', None))

    @define_state(MODE_MANUAL, False)
    def manual_multi_tone(self):
        if not self.manual_active:
            freqs0 = parse_frequency_input(self.static_ui.lineEdit_freq_ch0.text())
            freqs1 = parse_frequency_input(self.static_ui.lineEdit_freq_ch1.text())

            amp0 = self.static_ui.spinBox_amplitude.value()
            amp1 = self.static_ui.spinBox_amplitude1.value()

            self.static_ui.pushButton_SingleTone.setIcon(self.stop_icon)
            self.slope_ui.pushButton_Slope.setIcon(self.stop_icon)
            # self.static_ui.pushButton_MemoryReplay.setEnabled(False)
            self.manual_active = True

            yield self.queue_work(
                self._primary_worker,
                'program_manual',
                [freqs0, freqs1],
                [amp0, amp1]
            )
        else:
            self.static_ui.pushButton_SingleTone.setIcon(self.start_icon)
            self.slope_ui.pushButton_Slope.setIcon(self.start_icon)
            # self.static_ui.pushButton_MemoryReplay.setEnabled(True)
            self.manual_active = False
            yield self.queue_work(self._primary_worker, 'program_manual', None)

    @define_state(MODE_MANUAL, False)
    def dds_static(self):
        if not self.manual_active:
            freqs0 = parse_frequency_input(self.static_ui.lineEdit_freq_ch0.text())
            freqs1 = parse_frequency_input(self.static_ui.lineEdit_freq_ch1.text())

            amp0 = self.static_ui.spinBox_amplitude.value()
            amp1 = self.static_ui.spinBox_amplitude1.value()

            self.static_ui.pushButton_SingleTone.setIcon(self.stop_icon)
            self.slope_ui.pushButton_Slope.setEnabled(False)
            # self.static_ui.pushButton_MemoryReplay.setEnabled(False)
            self.manual_active = True

            yield self.queue_work(self._primary_worker, 'dds_static', [freqs0, freqs1], [amp0, amp1])
        else:
            self.static_ui.pushButton_SingleTone.setIcon(self.start_icon)
            self.slope_ui.pushButton_Slope.setEnabled(True)
            # self.static_ui.pushButton_MemoryReplay.setEnabled(True)
            self.manual_active = False
            yield self.queue_work(self._primary_worker, 'dds_static', None)

    @define_state(MODE_MANUAL, False)
    def dds_slope(self):
        if not self.manual_active:

            keep_final = self.slope_ui.checkBox_KeepFinal.isChecked()
            c_loop = self.slope_ui.checkBox_c_loop.isChecked()
            freqs0_i = parse_frequency_input(self.slope_ui.lineEdit_freq_i_ch0.text())
            freqs1_i = parse_frequency_input(self.slope_ui.lineEdit_freq_i_ch1.text())
            freqs0_f = parse_frequency_input(self.slope_ui.lineEdit_freq_f_ch0.text())
            freqs1_f = parse_frequency_input(self.slope_ui.lineEdit_freq_f_ch1.text())

            amp0 = self.slope_ui.spinBox_amplitude0_slope.value()
            amp1 = self.slope_ui.spinBox_amplitude1_slope.value()

            self.static_ui.pushButton_SingleTone.setEnabled(False)
            self.slope_ui.pushButton_Slope.setIcon(self.stop_icon)
            duration = self.slope_ui.spinBox_duration_slope.value()
            # self.static_ui.pushButton_MemoryReplay.setEnabled(False)
            self.manual_active = True

            yield self.queue_work(self._primary_worker, 'dds_slope', [freqs0_i, freqs1_i], [freqs0_f, freqs1_f], [amp0, amp1], duration, c_loop, keep_final)
        else:
            self.static_ui.pushButton_SingleTone.setEnabled(True)
            self.slope_ui.pushButton_Slope.setIcon(self.start_icon)
            # self.static_ui.pushButton_MemoryReplay.setEnabled(True)
            self.manual_active = False
            yield self.queue_work(self._primary_worker, 'dds_slope', None)
   
    @define_state(MODE_MANUAL, True)
    def reset_card(self):
        # self.ui.comboBox_memory.clear()
        self.queue_work(self._primary_worker,'card_reset')
        # self.ui.used_memory.setValue(0)
        # yield(self.queue_work(self._primary_worker,'program_manual',0.00))
        yield(self.queue_work(self._primary_worker,'card_reset'))
        