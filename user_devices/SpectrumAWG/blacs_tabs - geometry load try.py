from blacs.device_base_class import DeviceTab, MODE_MANUAL, MODE_BUFFERED, define_state
from qtutils.qt import QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QFileDialog
from qtutils import UiLoader
import os
import pyqtgraph as pg
from pyqtgraph import PlotWidget

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

        self.ui.pushButton_GeometryPlay.setIcon(self.start_icon)

        self.ui.pushButton_SingleTone.clicked.connect(lambda: self.manual_multi_tone())

        self.ui.pushButton_GeometryFile.setIcon(QtGui.QIcon(':/qtutils/fugue/folder'))
        self.ui.pushButton_GeometryFile.clicked.connect(self.select_memory_file)
        self.ui.pushButton_GeometryPlay.clicked.connect(self.geometry_play)
        self.ui.lineEdit_GeoemtryFile.setReadOnly(True)

        # self.ui.pushButton_refresh.setIcon(QtGui.QIcon(':/qtutils/fugue/arrow-circle-double'))
        # self.ui.pushButton_refresh.clicked.connect(lambda: self.refresh_dropdown_menu())

        self.ui.pushButton_reset.setIcon(QtGui.QIcon(':/qtutils/fugue/broom'))
        self.ui.pushButton_reset.clicked.connect(lambda: self.reset_card())

        self.ui.spinBox_NumSamples.valueChanged.connect(lambda: self.update_number_of_samples())
        self.ui.spinBox_sampleRate.valueChanged.connect(lambda: self.update_sample_rate())

        self.ui.comboBox_triggerSource.currentIndexChanged.connect(lambda: self.update_trigger_source())

        self.ui.comboBox_X0.currentIndexChanged.connect(lambda: self.update_Multi_IO('X0'))
        self.ui.comboBox_X1.currentIndexChanged.connect(lambda: self.update_Multi_IO('X1'))
        self.ui.comboBox_X2.currentIndexChanged.connect(lambda: self.update_Multi_IO('X2'))
        
        self.manual_active = False

        # Memory
        self.ui.used_memory.setMaximum(props["memory_segments"])


        self.auto_place_widgets(("Manual Generator",{"AWG":self.ui}))

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

        self.ui.lineEdit_GeoemtryFile.clear()
        for memory_index,instruction in self._final_values.items():
            self.ui.comboBox_memory.addItem(f"{memory_index} {instruction}")
        self.ui.lineEdit_GeoemtryFile.view().setMinimumWidth(self.ui.lineEdit_GeoemtryFile.view().sizeHintForColumn(0)+30)

        super().transition_to_manual(notify_queue,program=False)
        self.ui.used_memory.setValue(len(self._final_values))


    @define_state(MODE_MANUAL,False)
    def manual_single_tone(self):
        if not self.manual_active:
            frequency = self.ui.doubleSpinBox_frequency.value()
            self.ui.pushButton_SingleTone.setIcon(self.stop_icon)
            self.ui.pushButton_GeometryPlay.setEnabled(False)
            self.manual_active = True
            yield(self.queue_work(self._primary_worker,'program_manual',frequency))
        else:
            self.ui.pushButton_SingleTone.setIcon(self.start_icon)
            self.ui.pushButton_GeometryPlay.setEnabled(True)
            self.manual_active = False
            yield(self.queue_work(self._primary_worker,'program_manual', None))

    @define_state(MODE_MANUAL,False)
    def manual_multi_tone(self):
        if not self.manual_active:
            frequency = self.ui.doubleSpinBox_frequency.value()
            frequency1 = self.ui.doubleSpinBox_frequency1.value()
            amplitude = self.ui.spinBox_amplitude.value()
            amplitude1 = self.ui.spinBox_amplitude1.value()
            self.ui.pushButton_SingleTone.setIcon(self.stop_icon)
            self.ui.pushButton_GeometryPlay.setEnabled(False)
            self.manual_active = True
            yield(self.queue_work(self._primary_worker,'program_manual',[frequency, frequency1], [amplitude, amplitude1]))
        else:
            self.ui.pushButton_SingleTone.setIcon(self.start_icon)
            self.ui.pushButton_GeometryPlay.setEnabled(True)
            self.manual_active = False
            yield(self.queue_work(self._primary_worker,'program_manual', None))

    @define_state(MODE_MANUAL,False)
    def manual_memory_replay(self):
        if not self.manual_active:
            index = self.ui.lineEdit_GeoemtryFile.currentIndex()
            if index!=-1:
                self.ui.pushButton_GeometryPlay.setIcon(self.stop_icon)
                self.ui.pushButton_SingleTone.setEnabled(False)
                self.manual_active = True
            yield(self.queue_work(self._primary_worker,'program_manual',index))
        else:
            self.ui.pushButton_GeometryPlay.setIcon(self.start_icon)
            self.ui.pushButton_SingleTone.setEnabled(True)
            self.manual_active = False
            yield(self.queue_work(self._primary_worker,'program_manual',None))

    @define_state(MODE_MANUAL,False)
    def geometry_play(self,checked=False):
        if not self.manual_active:
            if not self.selected_memory_file:
                return  # or show a warning dialog

            self.ui.pushButton_GeometryPlay.setIcon(self.stop_icon)
            self.ui.pushButton_SingleTone.setEnabled(False)
            self.manual_active = True

            yield self.queue_work(
                self._primary_worker,
                'geometry_manual',
                self.selected_memory_file
            )

        else:
            self.ui.pushButton_GeometryPlay.setIcon(self.start_icon)
            self.ui.pushButton_SingleTone.setEnabled(True)
            self.manual_active = False

            yield self.queue_work(
                self._primary_worker,
                'geometry_manual',
                None
            )

    @define_state(MODE_MANUAL,False)           
    def select_memory_file(self, checked=False):
        file_path, _ = QFileDialog.getOpenFileName(
            None,
            "Select memory file",
            "",
            "HDF5 files (*.h5);;All files (*)"
        )

        if file_path:
            self.selected_memory_file = file_path
            self.ui.lineEdit_GeoemtryFile.setText(
                os.path.basename(file_path)
            )

    def on_memory_selected(self, index):
        if index >= 0:
            self.selected_memory_file = self.ui.lineEdit_GeoemtryFile.itemText(index)
        else:
            self.selected_memory_file = None

    @define_state(MODE_MANUAL,False)
    def refresh_dropdown_menu(self):
        self.ui.lineEdit_GeoemtryFile.clear()
        for memory_index,instruction in self._final_values.items():
            self.ui.comboBox_memory.addItem(f"{memory_index} {instruction}")
        self.ui.lineEdit_GeoemtryFile.view().setMinimumWidth(self.ui.lineEdit_GeoemtryFile.view().sizeHintForColumn(0)+30)
        
    @define_state(MODE_MANUAL, True)
    def reset_card(self):
        self.ui.comboBox_memory.clear()
        self.queue_work(self._primary_worker,'card_reset')
        self.ui.used_memory.setValue(0)
        # yield(self.queue_work(self._primary_worker,'program_manual',0.00))
        yield(self.queue_work(self._primary_worker,'card_reset'))
        