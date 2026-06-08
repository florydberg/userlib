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

        # Create UI
        self.ui = UiLoader().load(os.path.join(os.path.dirname(os.path.realpath(__file__)),"./blacs_widget.ui"))
        self.start_icon = QtGui.QIcon(':/qtutils/fugue/control')
        self.stop_icon = QtGui.QIcon(':/qtutils/fugue/control-stop-square')

        self.ui.pushButton_SingleTone.setIcon(self.start_icon)

        # self.ui.pushButton_MemoryReplay.setIcon(self.start_icon)
        
        # self.ui.pushButton_MemoryReplay.clicked.connect(lambda: self.manual_memory_replay())

        if not DDS_mode:
            self.ui.pushButton_SingleTone.clicked.connect(lambda: self.manual_multi_tone())
        else:
            self.ui.pushButton_SingleTone.clicked.connect(lambda: self.manual_DDS())

        # self.ui.pushButton_reset.setIcon(QtGui.QIcon(':/qtutils/fugue/broom'))
        # self.ui.pushButton_reset.clicked.connect(lambda: self.reset_card())

        self.ui.spinBox_NumSamples.valueChanged.connect(lambda: self.update_number_of_samples())

        self.ui.spinBox_sampleRate.valueChanged.connect(lambda: self.update_sample_rate())

        self.ui.comboBox_triggerSource.currentIndexChanged.connect(lambda: self.update_trigger_source())

        self.ui.comboBox_X0.currentIndexChanged.connect(lambda: self.update_Multi_IO('X0'))
        self.ui.comboBox_X1.currentIndexChanged.connect(lambda: self.update_Multi_IO('X1'))
        self.ui.comboBox_X2.currentIndexChanged.connect(lambda: self.update_Multi_IO('X2'))
        
        self.manual_active = False

        # Memory
        # self.ui.used_memory.setMaximum(props["memory_segments"])

        self.auto_place_widgets(("DDS mode",{"AWG":self.ui}))

        ## DDS slope widget
        self.dds_ui = UiLoader().load(os.path.join(os.path.dirname(os.path.realpath(__file__)),"./DDSslope_blacs_widget.ui"))

        self.dds_ui.pushButton_Slope.setIcon(self.start_icon)
        self.dds_ui.pushButton_Slope.clicked.connect(lambda: self.manual_slope())

        self.auto_place_widgets(("DDS slope", {"DDS_slope": self.dds_ui}))

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
        sample_rate=self.ui.spinBox_sampleRate.value()
        yield(self.queue_work(self._primary_worker, 'change_sampleRate', sample_rate))
    
    @define_state(MODE_MANUAL,False)
    def update_number_of_samples(self):
        num_samples=2**self.ui.spinBox_NumSamples.value()
        yield(self.queue_work(self._primary_worker, 'change_sampleNum', num_samples))
    
    @define_state(MODE_BUFFERED,False)
    def transition_to_manual(self,notify_queue,program=False):

        self.ui.comboBox_memory.clear()
        for memory_index,instruction in self._final_values.items():
            print(self._final_values.items())
            self.ui.comboBox_memory.addItem(f"{memory_index} {instruction}")
        self.ui.comboBox_memory.view().setMinimumWidth(self.ui.comboBox_memory.view().sizeHintForColumn(0)+30)

        super().transition_to_manual(notify_queue,program=False)
        self.ui.used_memory.setValue(len(self._final_values))

    @define_state(MODE_MANUAL,False)
    def manual_single_tone(self):
        if not self.manual_active:
            frequency = self.ui.doubleSpinBox_frequency.value()
            self.ui.pushButton_SingleTone.setIcon(self.stop_icon)
            self.dds_ui.pushButton_Slope.setIcon(self.stop_icon)
            # self.ui.pushButton_MemoryReplay.setEnabled(False)
            self.manual_active = True
            yield(self.queue_work(self._primary_worker,'program_manual',frequency))
        else:
            self.ui.pushButton_SingleTone.setIcon(self.start_icon)
            # self.ui.pushButton_MemoryReplay.setEnabled(True)
            self.manual_active = False
            yield(self.queue_work(self._primary_worker,'program_manual', None))

    @define_state(MODE_MANUAL, False)
    def manual_multi_tone(self):
        if not self.manual_active:
            freqs0 = parse_frequency_input(self.ui.lineEdit_freq_ch0.text())
            freqs1 = parse_frequency_input(self.ui.lineEdit_freq_ch1.text())

            amp0 = self.ui.spinBox_amplitude.value()
            amp1 = self.ui.spinBox_amplitude1.value()

            self.ui.pushButton_SingleTone.setIcon(self.stop_icon)
            self.dds_ui.pushButton_Slope.setIcon(self.stop_icon)
            # self.ui.pushButton_MemoryReplay.setEnabled(False)
            self.manual_active = True

            yield self.queue_work(
                self._primary_worker,
                'program_manual',
                [freqs0, freqs1],
                [amp0, amp1]
            )
        else:
            self.ui.pushButton_SingleTone.setIcon(self.start_icon)
            self.dds_ui.pushButton_Slope.setIcon(self.start_icon)
            # self.ui.pushButton_MemoryReplay.setEnabled(True)
            self.manual_active = False
            yield self.queue_work(self._primary_worker, 'program_manual', None)

    @define_state(MODE_MANUAL, False)
    def manual_DDS(self):
        if not self.manual_active:
            freqs0 = parse_frequency_input(self.ui.lineEdit_freq_ch0.text())
            freqs1 = parse_frequency_input(self.ui.lineEdit_freq_ch1.text())

            amp0 = self.ui.spinBox_amplitude.value()
            amp1 = self.ui.spinBox_amplitude1.value()

            self.ui.pushButton_SingleTone.setIcon(self.stop_icon)
            self.dds_ui.pushButton_Slope.setEnabled(False)
            # self.ui.pushButton_MemoryReplay.setEnabled(False)
            self.manual_active = True

            yield self.queue_work(self._primary_worker, 'manual_DDS', [freqs0, freqs1], [amp0, amp1])
        else:
            self.ui.pushButton_SingleTone.setIcon(self.start_icon)
            self.dds_ui.pushButton_Slope.setEnabled(True)
            # self.ui.pushButton_MemoryReplay.setEnabled(True)
            self.manual_active = False
            yield self.queue_work(self._primary_worker, 'manual_DDS', None)

    @define_state(MODE_MANUAL, False)
    def manual_slope(self):
        if not self.manual_active:
            freqs0_i = parse_frequency_input(self.dds_ui.lineEdit_freq_i_ch0.text())
            freqs1_i = parse_frequency_input(self.dds_ui.lineEdit_freq_i_ch1.text())
            freqs0_f = parse_frequency_input(self.dds_ui.lineEdit_freq_f_ch0.text())
            freqs1_f = parse_frequency_input(self.dds_ui.lineEdit_freq_f_ch1.text())

            amp0 = self.dds_ui.spinBox_amplitude0_slope.value()
            amp1 = self.dds_ui.spinBox_amplitude1_slope.value()

            self.ui.pushButton_SingleTone.setEnabled(False)
            self.dds_ui.pushButton_Slope.setIcon(self.stop_icon)
            duration = self.dds_ui.spinBox_duration_slope.value()
            # self.ui.pushButton_MemoryReplay.setEnabled(False)
            self.manual_active = True

            yield self.queue_work(self._primary_worker, 'manual_slope', [freqs0_i, freqs1_i], [freqs0_f, freqs1_f], [amp0, amp1], duration)
        else:
            self.ui.pushButton_SingleTone.setEnabled(True)
            self.dds_ui.pushButton_Slope.setIcon(self.start_icon)
            # self.ui.pushButton_MemoryReplay.setEnabled(True)
            self.manual_active = False
            yield self.queue_work(self._primary_worker, 'manual_slope', None)

    @define_state(MODE_MANUAL,False)
    def manual_memory_replay(self):
        if not self.manual_active:
            index = self.ui.comboBox_memory.currentIndex()
            if index!=-1:
                # self.ui.pushButton_MemoryReplay.setIcon(self.stop_icon)
                self.ui.pushButton_SingleTone.setEnabled(False)
                self.dds_ui.pushButton_Slope.setEnabled(False)
                self.manual_active = True
            yield(self.queue_work(self._primary_worker,'program_manual',index))
        else:
            # self.ui.pushButton_MemoryReplay.setIcon(self.start_icon)
            self.ui.pushButton_SingleTone.setEnabled(True)
            self.dds_ui.pushButton_Slope.setEnabled(True)
            self.manual_active = False
            yield(self.queue_work(self._primary_worker,'program_manual',None))

    @define_state(MODE_MANUAL,False)
    def refresh_dropdown_menu(self):
        self.ui.comboBox_memory.clear()
        for memory_index,instruction in self._final_values.items():
            self.ui.comboBox_memory.addItem(f"{memory_index} {instruction}")
        self.ui.comboBox_memory.view().setMinimumWidth(self.ui.comboBox_memory.view().sizeHintForColumn(0)+30)
        
    @define_state(MODE_MANUAL, True)
    def reset_card(self):
        self.ui.comboBox_memory.clear()
        self.queue_work(self._primary_worker,'card_reset')
        self.ui.used_memory.setValue(0)
        # yield(self.queue_work(self._primary_worker,'program_manual',0.00))
        yield(self.queue_work(self._primary_worker,'card_reset'))
        