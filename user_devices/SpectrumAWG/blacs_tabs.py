from blacs.device_base_class import DeviceTab, MODE_MANUAL, MODE_BUFFERED, define_state
from qtutils.qt import QtGui
from qtutils import UiLoader
import os


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
        self.ui.pushButton_MemoryReplay.setIcon(self.start_icon)
        self.ui.pushButton_SingleTone.clicked.connect(lambda: self.manual_single_tone())
        self.ui.pushButton_MemoryReplay.clicked.connect(lambda: self.manual_memory_replay())
        self.ui.pushButton_refresh.setIcon(QtGui.QIcon(':/qtutils/fugue/arrow-circle-double'))
        self.ui.pushButton_refresh.clicked.connect(lambda: self.refresh_dropdown_menu())
        self.manual_active = False
        # Memory
        self.ui.used_memory.setMaximum(props["memory_segments"])


        self.auto_place_widgets(("AWG",{"AWG":self.ui}))
     
    def get_front_panel_values(self):
        return self._final_values
    
    @define_state(MODE_BUFFERED,False)
    def transition_to_manual(self,notify_queue,program=False):
        super().transition_to_manual(notify_queue,program=False)
        #self.ui.used_memory.setValue(len(self._final_values))
        self.ui.used_memory.setValue(100)

    @define_state(MODE_MANUAL,False)
    def manual_single_tone(self):
        if not self.manual_active:
            frequency = self.ui.doubleSpinBox_frequency.value()
            self.ui.pushButton_SingleTone.setIcon(self.stop_icon)
            self.ui.pushButton_MemoryReplay.setEnabled(False)
            self.manual_active = True
            yield(self.queue_work(self._primary_worker,'program_manual',frequency))
        else:
            self.ui.pushButton_SingleTone.setIcon(self.start_icon)
            self.ui.pushButton_MemoryReplay.setEnabled(True)
            self.manual_active = False
            yield(self.queue_work(self._primary_worker,'program_manual',None))

    @define_state(MODE_MANUAL,False)
    def manual_memory_replay(self):
        if not self.manual_active:
            index = self.ui.comboBox_memory.currentIndex()
            if index!=-1:
                self.ui.pushButton_MemoryReplay.setIcon(self.stop_icon)
                self.ui.pushButton_SingleTone.setEnabled(False)
                self.manual_active = True
            yield(self.queue_work(self._primary_worker,'program_manual',index))
        else:
            self.ui.pushButton_MemoryReplay.setIcon(self.start_icon)
            self.ui.pushButton_SingleTone.setEnabled(True)
            self.manual_active = False
            yield(self.queue_work(self._primary_worker,'program_manual',None))

    @define_state(MODE_MANUAL,False)
    def refresh_dropdown_menu(self):
        self.ui.comboBox_memory.clear()
        for memory_index,instruction in self._final_values.items():
            self.ui.comboBox_memory.addItem(f"{memory_index} {instruction}")
        self.ui.comboBox_memory.view().setMinimumWidth(self.ui.comboBox_memory.view().sizeHintForColumn(0)+30)
        