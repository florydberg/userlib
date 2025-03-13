#####################################################################
#                                                                   #
# /MOGLabs_QRF.py                                                   #
#                                                                   #
# Copyright 2024, Florence University  -08/05/24                    #
#                                                                   #
# This file is part of the module labscript_devices, in the         #
# labscript suite (see http://labscriptsuite.org), and is           #
# licensed under the Simplified BSD License. See the license.txt    #
# file in the root of the project for the full license.             #
#                                                                   #
#####################################################################

# last modified by Andre FloRydberg 12/03/2025

import numpy as np
import time, logging

from labscript_devices import runviewer_parser, labscript_device, BLACS_tab, BLACS_worker
from labscript_utils.qtwidgets.toolpalette import ToolPaletteGroup
from labscript import Device, PseudoclockDevice, Pseudoclock, ClockLine, IntermediateDevice, DDSQuantity, config, LabscriptError, set_passed_properties
import labscript_utils.h5_lock, h5py
import labscript_utils.properties
from blacs.tab_base_classes import Worker, define_state, MODE_MANUAL, MODE_TRANSITION_TO_BUFFERED, MODE_TRANSITION_TO_MANUAL, MODE_BUFFERED
from blacs.device_base_class import DeviceTab
from user_devices.MOGlabsQRF.mogdevice import MOGDevice
from qtutils import UiLoader
import os
from qtutils.qt import QtGui
from PyQt5.QtWidgets import QWidget, QGridLayout, QCheckBox

if True:
    # reduce number of log entries in logfile (labscript-suite/logs/BLACS.log)
    log_level = [logging.CRITICAL, logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG, logging.NOTSET][2]

    # set number of channels
    MAX_NUM_CHANNELS = 4

    # min/max RF frequency in MHz
    MIN_RF_FREQ     = 5.0
    MAX_RF_FREQ     = 250.0
    DEFAULT_RF_FREQ = 20e+3

    # min/max RF amplitudes in dBm
    MIN_RF_AMP      = -50.0
    MAX_RF_AMP      = 33.0
    DEFAULT_RF_AMP = 0

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
    # we add epsilon(MAX_TIME) to clock_limit to avoid that small numerical errors cause problems.
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
    TABLE_CLOCK_RESOLUTION = 5e-6 # minimum time between table entries switching
    TABLE_MAX_BUS_RATE     = 1/TABLE_CLOCK_RESOLUTION
    TABLE_MAX_TIME         = ((2**32)-1)*TABLE_CLOCK_RESOLUTION # TODO: not clear what is largest time? maybe only 16bits?
    TABLE_CLOCK_LIMIT      = 1.0/(TABLE_CLOCK_RESOLUTION - 2*epsilon(TABLE_MAX_TIME))
    # limits when not in TABLE mode depends on actual FPGA board clock resolution
    NO_TABLE_CLOCK_RESOLUTION = NO_TABLE_MAX_TRIGGER_DELAY
    NO_TABLE_MAX_BUS_RATE     = 1/NO_TABLE_CLOCK_RESOLUTION
    def get_clock_limit(clock_resolution):
        return 1.0/(NO_TABLE_CLOCK_RESOLUTION - 2*epsilon(((2**32)-1)*clock_resolution))
    #print('Moglabs QFR: maximum bus rate %.3f MHz gives resolution %.3f ns and max time %.3f s (clock limit = bus rate + %.3f Hz)' % (MAX_BUS_RATE/1e6, CLOCK_RESOLUTION*1e9, MAX_TIME, CLOCK_LIMIT - MAX_BUS_RATE))

    # table options passed to worker
    FLAG_TABLE_MODE          = 1
    FLAG_TRIGGER_EACH_STEP  = 2

class QRF_DDS(IntermediateDevice):
    """
    wrapper class for DDS with table mode and trigger options.
    name = name of channel, must be a valid Python name
    parent_device = must be a MOGLabs_QRF device
    connection = must be 'channel %i' with %i = 0..3
    digital_gate = must contain 'device' = DigitalChannels intermediate device with free channel number given as 'connection'
    table_mode = if False: use enable/disable to switch RF on/off very fast.
                           channel frequency, amplitude, phase cannot change during the experiment.
                           set them once in experimental script, otherwise manual parameters are used.
                 if True: use table mode to program channel with every trigger (trigger_each_Step=True) or at the programmed time (trigger_each_Step=False)
                          this mode has a min 5us delay with jitter but allows the frequency, amplitude and phase to be changed during the experiment.
    trigger_each_step = used only with table_mode=True. if True for each change of the state of the channel a TTL signal is generated.
                 if False, a single trigger for the first change of the state of the channel is generated and the QRF executes the table at the programmed time.
                 if True the QRF will stay in sync with the experiment, but many triggers might be generated.
                 if False the QRF might get out of sync when the reference clock is not used.
    """

    def __init__(self, name, parent_device, connection, digital_gate=None, table_mode=True, trigger_each_step=False, freq_limits=None, freq_conv_class=None, freq_conv_params={},
                 amp_limits=None, amp_conv_class=None, amp_conv_params={}, phase_limits=None, phase_conv_class=None, phase_conv_params = {},
                 call_parents_add_device = True, **kwargs):

        # parent device must be MOGLabs_QRF device
        if not isinstance(parent_device, MOGLabs_QRF):
            raise LabscriptError("Device '%s' parent class is '%s' but must be 'MOGLabs_QRF'!" % (name, type(parent_device).__name__))

        # find parent FPGA board and check that this is correct
        # note: importing FPGA_board makes troubles, so have to check type instead of isinstance!
        #parent_board = parent_device.parent_board
        #if type(parent_board).__name__ != 'FPGA_board':
        #    raise LabscriptError("Device '%s' parent device is '%s' but must be 'FPGA_board'!" % (name, type(parent_board).__name__))

        # trigger device must be DigitalChannels intermediate device
        # note: importing FPGA_board makes troubles, so have to check type instead of isinstance!
        if not 'device' in digital_gate or not 'connection' in digital_gate:
            raise LabscriptError("Device '%s' give digital_gate={'device':DigitalChannels, 'connection':free channel number}!" % (self.name))
        if type(digital_gate['device']).__name__ != 'DigitalChannels':
            raise LabscriptError("Device '%s' trigger device is '%s' but must be 'DigitalChannels'!" % (name, type(digital_gate['device']).__name__))

        self.table_mode = table_mode
        self.trigger_each_step = trigger_each_step

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

        if True: # Andi: old version of labscript device.
            # create new DDS. self.DDS.gate contains new DigitalOutput used as trigger
            self.DDS = DDSQuantity(name, parent_device=self, connection=connection, digital_gate=digital_gate)
        else:
            # Andi: fast fix for incompatibility for digital gate with my newer labscript device.
            self.DDS = DDSQuantity(name, parent_device=self, connection=connection, digital_gate={})
            if digital_gate is not None:
                if 'device' in digital_gate and 'connection' in digital_gate:
                    dev = digital_gate.pop('device')
                    conn = digital_gate.pop('connection')
                    from user_devices.FPGA_device.labscript_device import DigitalOutput
                    self.DDS.gate = DigitalOutput(name + '_gate', dev, conn, **digital_gate)
                # Did they only put one key in the dictionary, or use the wrong keywords?
                elif len(digital_gate) > 0:
                    raise LabscriptError(
                        'You must specify the "device" and "connection" for the digital gate of %s.' % (self.name))

        # set default frequency in MHz
        self.DDS.frequency.default_value = DEFAULT_RF_FREQ

        self.DDS.amplitude.default_value = DEFAULT_RF_AMP

        # notify MOGLabs_QRF of new pseudoclock. this will adapt the clock_limt and clock_resolution to fastest clock
        parent_device.add_device(self.pseudoclock)

        # def setfreq(self, freq):

class MOGLabs_QRF(PseudoclockDevice):
    """
    MOGLabs QRF device.
    init with:
    name = allowed python name
    trigger_device = must be FPGA_board
    addr = address for MOGDevice.__init__
    port = prot for MOGDevice.__init__
    worker_args = arguments passed to MOGLabs_QRF_Worker
    """

    description = 'QRF'
    allowed_children = [Pseudoclock]

    # these values will be updated in add_device for fastest channels
    # TODO: inserted temporarily - should be updated later by fastest DDS channel.
    #       the problem here is that the channels can have different clock rates and limits which is not intended here.
    #       a solution would be to create one QRF device for each channel but only one worker can talk to the real device. possible but not practical.
    clock_limit = get_clock_limit(1e-6)
    clock_resolution = 1e-6
    trigger_delay = 1e-6
    trigger_minimum_duration = 5e-6

    @set_passed_properties(
        property_names={'connection_table_properties': ['addr', 'port', 'worker_args']}
    )
    def __init__(self, name, parent_device, addr=None, port=7802, worker_args=None):
        self.BLACS_connection = '%s,%s' % (addr, str(port))

        self.name = name
        self.parent_device = parent_device # will be replaced with digital channel of fastest QRF_DDS
        self.parent_board  = parent_device

        # parent device must be FPGA_board
        # note: importing FPGA_board makes troubles, so have to check type instead of isinstance!
        #if type(parent_device).__name__ != 'FPGA_board':
        #    raise LabscriptError("Device '%s' trigger class is '%s' but must be 'FPGA_board'!" % (self.name, type(parent_device).__name__))

        if parent_device is None:
            self.is_primary = True
            self.primary_board = None
            # inputs = default_in_prim
            # outputs = default_out_prim
        else:
            self.is_primary = False
            self.primary_board = True
            # inputs = default_in_sec
            # outputs = default_out_sec


        # init parent class. we must give a trigger_device and trigger_connection (name seems not to matter)
        # this will create a Trigger device which needs to have parent_device = DigitalOut
        # we will fill this in as soon as QRF_DDS channels are created and clockline is added in add_device
        print(f"parent device of QRF: '{parent_device}")
        PseudoclockDevice.__init__(self, name, trigger_device=parent_device, trigger_connection='trigger')
        # add QRF to list of secondary boards. this is needed, otherwise generate_code is not called.
        #self.parent_board.add_device(self)

    def add_device(self, device):
        # called with device = Pseudoclock from child channel QRF_DDS
        print('QRF add_device called for device',device.name)
        Device.add_device(self, device)

        if False:
            # we need to provide a valid DigitalChannel as trigger_device also for the MOGLabs_QRF, otherwise start() will give an error.
            # we choose the fastest channel for this.
            # TODO: I cannot say at the moment if this has negative side-effects.
            #       its also strange that for the Secondary boards this is NOT needed!?
            IM = device.child_devices[0].child_devices[0]
            clock_limit = IM.clock_limit
            if self.clock_limit is None or clock_limit > self.clock_limit:
                self.clock_limit = clock_limit
                self.clock_resolution = IM.clock_resolution
                self.trigger_device.parent_device = IM.DDS.gate

    def generate_code(self, hdf5_file):

        print(f"'{self.name}' generating code...")

        # create list of times and raw_data for each device
        PseudoclockDevice.generate_code(self, hdf5_file)

        grp = self.init_device_group(hdf5_file)
        dtypes = [('time', np.uint32), ('freq', np.uint32), ('amp', np.uint16), ('phase', np.uint16), ('pid_setpoint', np.uint16)]

        # get values of all channels. channels might have different numbers of entries.
        for pseudoclock in self.child_devices:
            #print(pseudoclock)
            for clockline in pseudoclock.child_devices:
                #print(clockline)
                for IM in clockline.child_devices:
                    if False:
                        print(IM)
                    for dds in IM.child_devices:
                        #print(dds.name)
                        try:
                            prefix, channel = dds.connection.split()
                            channel = int(channel)
                        except:
                            raise LabscriptError('%s has invalid connection string: \'%s\'. ' % (dds.name, str(dds.connection)) + 'Format must be \'channel n\' with n from 0 to 4.')

                        gate = dds.gate
                        print(gate.name)
                        gate_cl = gate.parent_device.parent_device
                        gate_ps = gate_cl.parent_device
                        if False:
                            print(gate_ps.times[gate_cl])
                            print(gate.raw_output)
                            print(gate.child_devices)

                        # for connection in DDSs:
                        #     if connection in range(2):
                        #         # Dynamic DDS
                        #         dds = DDSs[connection]
                        #         print(dds.frequency.scale_factor)
                        #     else:
                        #         raise LabscriptError('%s %s has invalid connection string: \'%s\'. '%(dds.description,dds.name,str(dds.connection)) +
                        #                              'Format must be \'channel n\' with n from 0 to 4.')

                        times = pseudoclock.times[clockline]
                        if False:
                            print(f"'{dds.name}' times: {times}")
                        #print(f"'{self.name}' DDSs: {DDSs}")

                        # TODO: enable/disable act on the TTL. in table mode we need to know the RF level and set amp to minimum / last level.
                        #       if level is never set use manual values

                        out_table = np.zeros(len(times), dtype=dtypes)
                        out_table['freq'].fill(DEFAULT_RF_FREQ)

                        #print(f"Channel {connection} output: {[dds.frequency.raw_output,dds.amplitude.raw_output,dds.phase.raw_output]}")
                        # The last two instructions are left blank, for BLACS
                        # to fill in at program time.
                        out_table['time'][:]  = times
                        out_table['freq'][:]  = dds.frequency.raw_output
                        out_table['amp'][:]   = dds.amplitude.raw_output
                        out_table['phase'][:] = dds.phase.raw_output
                        out_table['pid_setpoint'][:] = dds.setpoint.raw_output #"setpoint_flag" #dds.PIDbox.setpoint

                        if IM.table_mode:
                            grp.create_dataset('TABLE_DATA%i'%channel, compression=config.compression, data=out_table)
                            flags = (FLAG_TABLE_MODE) | (FLAG_TRIGGER_EACH_STEP if IM.trigger_each_step else 0)
                            grp.create_dataset('TABLE_OPT%i' % channel, compression=config.compression, data=np.array([flags], dtype=np.uint8))
                        else:
                            grp.create_dataset('STATIC_DATA%i'%channel, compression=config.compression, data=out_table)                        

                        if False:
                            print(f"'{dds.name}' generate_code, out_table:\n time/freq/amp/phase\n", out_table)

class power_check_boxes(QWidget):
    # Andi: power check boxes for each DDS
    labels = ['signal', 'amplifier', 'both', 'PID']  # labels for check boxes

    def __init__(self, parent, name, channel, signal=False, amplifier=False, PID=False, align_horizontal=False):
        super(power_check_boxes, self).__init__(parent._ui)

        # init class
        self.parent    = parent                 # parent (DeviceTab instance)
        self.name      = name                   # channel name in connection table (string)
        self.channel   = channel                # channel number (integer)
        self.signal    = signal                 # initial state of signal check box (bool)
        self.amplifier = amplifier              # initial state of amplifier check box (bool)
        self.both      = signal and amplifier   # initial state of both check box (bool)
        self.PID       = PID                    # initial state of PID

        # create layout
        grid = QGridLayout(self)
        self.setLayout(grid)

        # create check boxes
        states  = [signal, amplifier, signal and amplifier, PID]
        connect = [self.onSignal, self.onAmp, self.onBoth, self.onPID]
        self.cb = []
        for i,name in enumerate(self.labels):
            cb = QCheckBox(name)
            cb.setChecked(states[i])
            cb.clicked.connect(connect[i])
            self.cb.append(cb)
            if align_horizontal: grid.addWidget(cb, 0, i)
            else:                grid.addWidget(cb, i, 0)

    def onSignal(self, state):
        # 'signal' clicked: manually insert event into parent event queue. see tab_base_classes.py @define_state(MODE_MANUAL, True)
        self.parent.event_queue.put(allowed_states=MODE_MANUAL, queue_state_indefinitely=True, delete_stale_states=False,
                                    data=[self._onSignal, [[self.channel, state], {}]])

    def onAmp(self, state, both=False):
        # 'amplifier' clicked: manually insert event into parent event queue. see tab_base_classes.py @define_state(MODE_MANUAL, True)
        self.parent.event_queue.put(allowed_states=MODE_MANUAL, queue_state_indefinitely=True, delete_stale_states=False,
                                    data=[self._onAmp, [[self.channel, state], {}]])

    def onBoth(self, state):
        # 'both' clicked: manually insert event into parent event queue. see tab_base_classes.py @define_state(MODE_MANUAL, True)
        self.parent.event_queue.put(allowed_states=MODE_MANUAL, queue_state_indefinitely=True, delete_stale_states=False,
                                    data=[self._onBoth, [[self.channel, state], {}]])

    def _onSignal(self, parent, channel, state):
        # executed by QT main thread (tab_base_classes.py Tab::mainloop). must be generator (with yield).
        info = "'%s' %s signal" % (self.name, 'enable' if state else 'disable')
        result = yield (self.parent.queue_work(self.parent.primary_worker, 'onSignal', channel, state))
        if (result is not None) and result:
            self.signal = state
            print(info)
            self.cb[0].setChecked(self.signal)
            self.set_both()
        else:
            print(info + ' failed!')
            self.cb[0].setChecked(self.signal)

    def _onAmp(self, parent, channel, state):
        # executed by QT main thread (tab_base_classes.py Tab::mainloop). must be generator (with yield).
        info = "'%s' %s amplifier" % (self.name, 'enable' if state else 'disable')
        result = yield (self.parent.queue_work(self.parent.primary_worker, 'onAmp', channel, state))
        if (result is not None) and result:
            self.amplifier = state
            print(info)
            self.cb[1].setChecked(self.amplifier)
            self.set_both()
        else:
            print(info + ' failed!')
            self.cb[1].setChecked(self.amplifier)

    def _onBoth(self, parent, channel, state):
        # executed by QT main thread (tab_base_classes.py Tab::mainloop). must be generator (with yield).
        info = "'%s' %s signal & amplifier" % (self.name, 'enable' if state else 'disable')
        result = yield (self.parent.queue_work(self.parent.primary_worker, 'onBoth', channel, state))
        if (result is not None) and result:
            self.signal    = state
            self.amplifier = state
            print(info)
            self.cb[0].setChecked(self.signal)
            self.cb[1].setChecked(self.amplifier)
            self.set_both()
        else:
            print(info + ' failed!')
            self.cb[2].setChecked(self.both)

    def set_both(self):
        # returns new checked state of 'both' checkbox
        # changes state only when signal and amplifier are both on or both off
        # this allows to click on 'both' to perform the last selection for both.
        if self.both:
            self.both = self.signal or self.amplifier
        else:
            self.both = self.signal and self.amplifier
        self.cb[2].setChecked(self.both)

    def get_save_data(self, data):
        "save current settings to data dictionary"
        state = (4 if self.both else 0)|(2 if self.amplifier else 0)|(1 if self.signal else 0)
        #print('get_save_data state =',state)
        data[self.name] = state

    def restore_save_data(self, data):
        "restore saved settings from data dictionary"
        if self.name in data:
            state = data[self.name]
            #print('restore_save_data state =', state)
            signal = (state & 1) == 1
            amp    = (state & 2) == 2
            both   = (state & 4) == 4
            if (signal == amp) and ((self.signal != signal) or (self.amplifier != amp)):
                self.onBoth(signal)
            else:
                if self.signal != signal: self.onSignal(signal)
                if self.amplifier != amp: self.onAmp(amp)
                self.both = both
                self.cb[2].setChecked(both)
    
    def  onPID(self, state):
        # 'PID' clicked: manually insert event into parent event queue. see tab_base_classes.py @define_state(MODE_MANUAL, True)
        self.parent.event_queue.put(allowed_states=MODE_MANUAL, queue_state_indefinitely=True, delete_stale_states=False,
                                    data=[self._onPID, [[self.channel, state], {}]])

    def _onPID(self, parent, channel, state):
        # executed by QT main thread (tab_base_classes.py Tab::mainloop). must be generator (with yield).
        info = "'%s' PID channel %i is %s" % (self.name, channel, 'enable' if state else 'disable')
        result = yield (self.parent.queue_work(self.parent.primary_worker, 'onPID', channel, state))
        if (result is not None) and result:
            self.PID = state
            print(info)
            self.cb[1].setChecked(self.PID)
            self.set_both()
        else:
            print(info + ' failed!')
            self.cb[1].setChecked(self.PID)

    def update(self, remote_values):
        "update values from remote_values"
        state = remote_values['STATUS']
        signal = (state & 1) == 1
        amp    = (state & 2) == 2
        both   = (state & 4) == 4
        if (signal == amp) and ((self.signal != signal) or (self.amplifier != amp)):
            self.onBoth(signal)
        else:
            if self.signal != signal: self.onSignal(signal)
            if self.amplifier != amp: self.onAmp(amp)
            self.both = both
            self.cb[2].setChecked(both)

        state = remote_values['PID']['STATUS']
        if isinstance(state, str) and (state == 'DISABLED'):
            self.PID = False
        else:
            self.PID = False
        self.cb[2].setChecked(self.PID)

class PID_boxes(QWidget):
    # Andre: PID box for each DDS
    labels = ['Proportional', 'Integral', 'Derivative', 'Setpoint', 'Invert']  # labels for check boxes

    def __init__(self, parent, name, channel, Proportional=False, Integral=False, Derivative=False, Setpoint=False, Invert=False):
        super(PID_boxes, self).__init__(parent._ui)

        # init class
        self.parent       = parent                 # parent (DeviceTab instance)
        self.name         = name                   # channel name in connection table (string)
        self.channel      = channel                # channel number (integer)
        self.Proportional = Proportional           # initial state of signal check box (bool)
        self.Integral     = Integral               # initial state of amplifier check box (bool)
        self.Derivative   = Derivative             # initial state of both check box (bool)
        self.Setpoint     = Setpoint               # initial state of PID
        self.Invert       = Invert                 # initial state of PID
        self.error_display= False
        self.ErrorSignal  = 500

        # Capabilities
        self.base_units = {'proportional': ' ', 'integral': ' ', 'derivative': ' '}
        self.base_min = {'proportional': 0, 'integral': 0, 'derivative': -1}
        self.base_max = {'proportional': 100, 'integral': 100, 'derivative': +1}
        self.base_step = {'proportional': 0, 'integral': 0, 'derivative': 0}
        self.base_decimals = {'proportional': 3, 'integral': 3, 'derivative': 1}
        self.num_DDS = MAX_NUM_CHANNELS

        # Create P.I.D. objects
        PID_prop = {}
        for i in range(self.num_DDS):  # 4 is the number of DDS outputs on this device
            PID_prop['channel %d' % i] = {}
            for subchnl in ['proportional', 'integral', 'derivative']:
                PID_prop['channel %d' % i][subchnl] = {'base_unit': self.base_units[subchnl],
                                                       'min': self.base_min[subchnl],
                                                       'max': self.base_max[subchnl],
                                                       'step': self.base_step[subchnl],
                                                       'decimals': self.base_decimals[subchnl]
                                                       }

        # Create UI
        self.ui = UiLoader().load(os.path.join(os.path.dirname(os.path.realpath(__file__)),"./PID_blacs_widget.ui"))
        # self.ui.pushButton_invert.setIcon(QtGui.QIcon(':/qtutils/fugue/arrow-circle-double'))
        self.start_icon = QtGui.QIcon(':/qtutils/fugue/control')
        self.stop_icon = QtGui.QIcon(':/qtutils/fugue/control-stop-square')
        self.ui.pushButton_errorSignal.setIcon(self.start_icon)
        self.ui.pushButton_errorSignal.clicked.connect(lambda: self.display_errorSignal())
        # self.ui.pushButton_invert.clicked.connect(lambda: self.invertPID())
        self.ui.doubleSpinBox_Proportional.valueChanged.connect(lambda: self.set_proportional())
        self.ui.slider_Proportional.valueChanged.connect(lambda: self.slide_proportional())
        # self.ui.slider_Proportional.sliderReleased.connect(lambda: self.set_proportional())
        self.ui.doubleSpinBox_Integral.valueChanged.connect(lambda: self.set_integral())
        self.ui.slider_Integral.valueChanged.connect(lambda: self.slide_integral())
        self.ui.doubleSpinBox_Derivative.valueChanged.connect(lambda: self.set_derivative())
        self.ui.slider_Derivative.valueChanged.connect(lambda: self.slide_derivative())
        self.ui.doubleSpinBox_PreGain.valueChanged.connect(lambda: self.set_pregain())
        self.ui.slider_PreGain.valueChanged.connect(lambda: self.slide_pregain())
        self.ui.doubleSpinBox_SetPoint.valueChanged.connect(lambda: self.set_setpoint())

        self.ui.slider_ErrorSignal.setSliderPosition(self.ErrorSignal)

        self.parent.auto_place_widgets((f"P.I.D. settings for channel {self.channel}",{"P.I.D.":self.ui}))

        # yield(self.parent.queue_work(self.parent.primary_worker,'print_main', notify_queue))

    def slide_pregain(self):
        value = self.ui.slider_PreGain.value()
        self.ui.doubleSpinBox_PreGain.setValue(value)

    def set_pregain(self):
        value = self.ui.doubleSpinBox_PreGain.value()
        self.ui.slider_PreGain.setSliderPosition(value)
        self.parent.event_queue.put(allowed_states=MODE_MANUAL, queue_state_indefinitely=True, delete_stale_states=False,
                                    data=[self._set_pregain, [[self.channel, value], {}]])

    def _set_pregain(self, parent, channel, value=0):
        info = "'%s' PID proportional set to %s" % (self.name, value)
        result = yield (self.parent.queue_work(self.parent.primary_worker, 'pregainPID', channel, value))
        if (result is not None) and result:
            print(info)
        else:
            print(info + ' failed!')        

    def slide_proportional(self):
        value = self.ui.slider_Proportional.value()
        self.ui.doubleSpinBox_Proportional.setValue(value)
        
    def set_proportional(self):
        value = self.ui.doubleSpinBox_Proportional.value()
        self.ui.slider_Proportional.setSliderPosition(value)
        self.parent.event_queue.put(allowed_states=MODE_MANUAL, queue_state_indefinitely=True, delete_stale_states=False,
                                    data=[self._setPID, [[self.channel, 'P', value], {}]])

    def slide_integral(self):
        value = self.ui.slider_Integral.value()
        self.ui.doubleSpinBox_Integral.setValue(value)

    def set_integral(self):
        value = self.ui.doubleSpinBox_Integral.value()
        self.ui.slider_Integral.setSliderPosition(value)
        self.parent.event_queue.put(allowed_states=MODE_MANUAL, queue_state_indefinitely=True, delete_stale_states=False,
                                    data=[self._setPID, [[self.channel, 'I', value], {}]])

    def slide_derivative(self):
        value = self.ui.slider_Derivative.value()
        self.ui.doubleSpinBox_Derivative.setValue(value)

    def set_derivative(self):
        value = self.ui.doubleSpinBox_Derivative.value()
        self.ui.slider_Derivative.setSliderPosition(value)
        self.parent.event_queue.put(allowed_states=MODE_MANUAL, queue_state_indefinitely=True, delete_stale_states=False,
                                    data=[self._setPID, [[self.channel, 'D', value], {}]])

    def _setPID(self, parent, channel, type, value):
        info = "'%s' PID channel %i set %s to %s" % (self.name, channel, type, value)
        result = yield (self.parent.queue_work(self.parent.primary_worker, 'setPID', channel, type, value))
        print(info + (' ok' if (result is not None) and result else ' failed'))

    def set_setpoint(self):
        value = self.ui.doubleSpinBox_SetPoint.value()
        self.parent.event_queue.put(allowed_states=MODE_MANUAL, queue_state_indefinitely=True, delete_stale_states=False,
                                    data=[self._set_setpoint, [[self.channel, value], {}]])
        
    def _set_setpoint(self, parent, channel, value):
        info = "'%s' PID setpoint set to %s" % (self.name, value)
        result = yield (self.parent.queue_work(self.parent.primary_worker, 'setpointPID', channel, value))
        if (result is not None) and result:
            print(info)
        else:
            print(info + ' failed!')                

    def invertPID(self, state=True):
        # 'PID' clicked: manually insert event into parent event queue. see tab_base_classes.py @define_state(MODE_MANUAL, True)
        self.parent.event_queue.put(allowed_states=MODE_MANUAL, queue_state_indefinitely=True, delete_stale_states=False,
                                    data=[self._invertPID, [[self.channel, state], {}]])

    def _invertPID(self, parent, channel, state=True):
        info = "'%s' PID polarity got inverted to %s" % (self.name, 'ON' if state else 'OFF')
        result = yield (self.parent.queue_work(self.parent.primary_worker, 'invertPID', channel, state))
        if (result is not None) and result:
            print(info)
        else:
            print(info + ' failed!')

    def display_errorSignal(self):
        if not self.error_display:
            self.ui.pushButton_errorSignal.setIcon(self.stop_icon)
            self.error_display = True
            self.parent.event_queue.put(allowed_states=MODE_MANUAL, queue_state_indefinitely=True, delete_stale_states=False,
                                        data=[self._display_errorSignal, [[self.channel, ], {}]])
        else:
            self.ui.pushButton_errorSignal.setIcon(self.start_icon)
            self.error_display = False
            self.ui.slider_ErrorSignal.setSliderPosition(500)        
            
    def _display_errorSignal(self, parent, channel):
        result = yield(self.parent.queue_work(self.parent.primary_worker,'errorPID', channel) )
        if (result is not None):
            self.ui.slider_ErrorSignal.setSliderPosition(result)
            print('displaying error')
        else:
            self.ui.slider_ErrorSignal.setSliderPosition(0)
            print('displaying error'+ ' failed!')

    def update(self, remote_values):
        "update values from remote_values"
        self.ui.doubleSpinBox_Proportional.setValue(remote_values['P'])
        self.ui.doubleSpinBox_Integral.setValue(remote_values['I'])
        self.ui.doubleSpinBox_Derivative.setValue(remote_values['D'])

@BLACS_tab
class MOGLabs_QRF_Tab(DeviceTab):
    def initialise_GUI(self):
        # Andi: reduce number of log entries in logfile (labscript-suite/logs/BLACS.log)
        self.logger.setLevel(log_level)

        # Capabilities
        self.base_units = {'freq': 'MHz', 'amp': 'dBm', 'phase': 'Degrees'}
        self.base_min = {'freq': MIN_RF_FREQ, 'amp': MIN_RF_AMP, 'phase': MIN_RF_PHASE}
        self.base_max = {'freq': MAX_RF_FREQ, 'amp': MAX_RF_AMP, 'phase': MAX_RF_PHASE}
        self.base_step = {'freq': 1.0, 'amp': 1.0, 'phase': 1.0}
        self.base_decimals = {'freq': 3, 'amp': 2, 'phase': 3}  # TODO: find out what the phase precision is! #freq was at 6
        self.num_DDS = MAX_NUM_CHANNELS

        # Create DDS Output objects
        dds_prop = {}
        for i in range(self.num_DDS):  # 4 is the number of DDS outputs on this device
            dds_prop['channel %d' % i] = {}
            for subchnl in ['freq', 'amp', 'phase']:
                dds_prop['channel %d' % i][subchnl] = {'base_unit': self.base_units[subchnl],
                                                       'min': self.base_min[subchnl],
                                                       'max': self.base_max[subchnl],
                                                       'step': self.base_step[subchnl],
                                                       'decimals': self.base_decimals[subchnl]
                                                       }
        # Create the output objects
        self.create_dds_outputs(dds_prop)
        # Create widgets for output objects
        dds_widgets, ao_widgets, do_widgets = self.auto_create_widgets()
        # and auto place the widgets in the UI
        self.auto_place_widgets(("DDS Outputs", dds_widgets))

        connection_object = self.settings['connection_table'].find_by_name(self.device_name)
        connection_table_properties = connection_object.properties

        self.addr = connection_table_properties['addr']
        self.port = connection_table_properties['port']
        self.worker_args = connection_table_properties['worker_args']

        # Create and set the primary worker
        self.create_worker("main_worker", MOGLabs_QRF_Worker, {'addr': self.addr, 'port': self.port, 'worker_args': self.worker_args})
        self.primary_worker = "main_worker"

        # Set the capabilities of this device
        self.supports_remote_value_check(True)
        self.supports_smart_programming(True)

        # get dictionary of channels with names in connection table
        channels = {}
        for pseudoclock in connection_object.child_list.values():
            #print(pseudoclock.name)
            for clockline in pseudoclock.child_list.values():
                #print(clockline.name)
                for IM in clockline.child_list.values():
                    #print(IM.name)
                    for name, child in IM.child_list.items():
                        channels[child.parent_port] = name
        print(channels)

        # add check boxes to enable signal/power/both:
        place_below = False # True = below DDS frame, False = right of DDS frame
        layout = self.get_tab_layout()
        index = layout.count()
        self.power_cb = [None for _ in range(MAX_NUM_CHANNELS)]
        for i in range(index):
            widget = layout.itemAt(i).widget()
            if widget is not None:
                children = widget.findChildren(ToolPaletteGroup)
                for child in children:
                    if 'DDS Outputs' in child._widget_groups:
                        index, toolpalette, button = child._widget_groups['DDS Outputs']
                        for j,dds in enumerate(toolpalette._widget_list):
                            layout = dds._layout
                            channel = dds._hardware_name
                            try:
                                channel_index = int(channel.split(' ')[-1])
                            except ValueError:
                                print("unexpected channel name '%s'?")
                                break
                            cb = power_check_boxes(parent=self, name=channels[channel], channel=channel_index, align_horizontal=place_below)
                            if place_below: layout.addWidget(cb)
                            else:           layout.addWidget(cb,1,1)
                            if j < MAX_NUM_CHANNELS:
                                self.power_cb[j] = cb
                            else:
                                print('error: maximum channels %i specified but %i existing!?' % (MAX_NUM_CHANNELS, len(toolpalette._widget_list)))
                                exit()

        # Andre: PID SECTION #######################################################################
     

        if True:
            self.pid_box = [None for _ in range(MAX_NUM_CHANNELS)]
            for ch in range(4):
                self.pid_box[ch] = PID_boxes(parent=self, name='PID', channel=ch)
            

    def get_save_data(self):
        # Andi: save user selection on shutdown
        data = {}
        for cb in self.power_cb:
            cb.get_save_data(data)
        #print("'%s' get_save_data:" % self.device_name, data)
        return data

    def restore_save_data(self, data):
        # Andi: restore user selection on restart
        # print("'%s' restore_save_data:" % self.device_name, data)
        for cb in self.power_cb:
            cb.restore_save_data(data)

    @define_state(MODE_MANUAL | MODE_BUFFERED, True)
    def get_error( self, channel, notify_queue, control, error_slider):
        if control:
            error_values = yield(self.queue_work(self.primary_worker, 'errorPID', channel))
            return error_values

    # Andi: we use check_remote_values to get state of all GUI elements of QRF incl. ON/OFF, PID.
    # problem:
    #       - this function overwrites super = blacs.device_base_classe.check_remote_values
    #       - the decorator blacs.tab_base_classes.define_state is also used in the super class
    #         and does NOT call blacs.device_base_classe.check_remote_values directly but inserts into the event_queue.
    #       - this has the unexpected side-effect that when we call super here it is NOT immediately executed!
    #         but only AFTER we return here. This causes that self._last_remote_values here is NOT updated!
    # solution:
    #       - we insert another function self._update_remote_values into event queue which is called
    #         after blacs.device_base_classe.check_remote_values returns
    #       - its a bit messy and inefficient due to the many events but it works and I do not know how to do it better.
    # alternative:
    #       - call here: yield(self.queue_work(self._primary_worker,'check_remote_values'))
    #         to get the remote values from the worker and in the second call from the super
    #         only return the already obtained values. but this is most likeley even less efficient.

    @define_state(MODE_MANUAL,True)
    def check_remote_values(self):
        super(MOGLabs_QRF_Tab, self).check_remote_values()
        self.event_queue.put(allowed_states=MODE_MANUAL,
                             queue_state_indefinitely=True,
                             delete_stale_states=False,
                             data=[self._update_remote_values, [[], {}]])
        #print('check_remove_values:', self._last_remote_values)

    def _update_remote_values(self, parent):
        #print('update_remove_values:', self._last_remote_values)
        for ch in range(4):
            ch_data = self._last_remote_values['channel %i'%ch]
            self.power_cb[ch].update(ch_data)
            self.pid_box[ch].update(ch_data['PID'])

# @BLACS_worker # Andi: disabled due to warning
class MOGLabs_QRF_Worker(Worker):
    def init(self):
        global h5py
        import labscript_utils.h5_lock, h5py

        # Andi: reduce number of log entries in logfile (labscript-suite/logs/BLACS.log)
        self.logger.setLevel(log_level)

        self.PIDstatus={}
        self.smart_cache = {'TABLE_DATA': ''}
        self.smart_cache = {'STATIC_DATA': ''}

        # Andre: to rescue table-stucked channels
        if self.reconnect('init'):
            for channel in range(MAX_NUM_CHANNELS): 
                try:
                    self.dev.cmd(f'TABLE,STOP,{channel+1}') 
                    self.dev.cmd(f'TABLE,CLEAR,{channel+1}')  
                    self.dev.cmd(f'MODE,%i,NSB' % (channel+1))
                    self.dev.cmd(f"ON,{channel+1},SIG")
                    print(f"Ch {channel} end of table mode")
                except:
                    print(f"Ch {channel} already in normal mode")
                    self.dev.cmd('MODE,%i,NSB' % (channel+1))
                    self.dev.cmd(f"ON,{channel+1},SIG")
                self.PIDstatus[channel]=False
                ask=self.dev.ask(f'PID,STATUS,{channel+1}')
                print(f'PID of channel {channel} is {str(ask)}')

    def reconnect(self, name):
        # Andi: try to connect to device. returns True on success, otherwise False.
        #       check if self.dev is None if device is connected or not and call this again.
        try:
            self.dev = MOGDevice(self.addr, self.port)
        except Exception: # on Linux gives OSError, on Windows dont know
            self.dev = None
            print('%s: no connection.' % (name))
            return False
        self.dev.flush()
        return True

    def check_remote_values(self):
        # Andi: try to reconnect. return 0's on failure.
        results = {}
        if (self.dev is None) and not self.reconnect('check_remote_values'):
            for i in range(MAX_NUM_CHANNELS):
                results['channel %d' % i] = {}
                results['channel %d' % i]['freq'] = 0.0
                results['channel %d' % i]['amp']  = 0.0
                results['channel %d' % i]['phase'] = 0.0
            return results
        # Get the currently output values:
        for i in range(MAX_NUM_CHANNELS):
            results['channel %d' % i] = {}
            freq = float(self.dev.ask('FREQ,%d' % (i + 1)).split()[0])
            amp = float(self.dev.ask('POW,%d' % (i + 1)).split()[0])
            phase = float(self.dev.ask('PHASE,%d' % (i + 1)).split()[0])

            results['channel %d' % i]['freq'] = freq
            results['channel %d' % i]['amp'] = amp
            results['channel %d' % i]['phase'] = phase
            # print(results)

            # signal (1), amplifier (2) or both (3)
            rsp = self.dev.ask(f'STATUS,{i + 1}')
            results['channel %d' % i]['STATUS'] = int(rsp)

            pid = {}
            rsp = self.dev.ask(f'PID,STATUS,{i + 1}')
            if rsp.startswith('ENABLED'):
                pid['STATUS'] = rsp.split(',')[1].strip()
            else:
                pid['STATUS'] = rsp
            for q in ['P','I','D']:
                rsp = self.dev.ask(f'PID,GAIN,{i+1},{q})')
                pid[q] = int(round(float(rsp)*100)) # value in %
            results['channel %d' % i]['PID'] = pid

        #print('remote values =', results)
        return results

    def program_manual(self, front_panel_values):
        # try to reconnect. return on failure.
        if (self.dev is None) and (not self.reconnect('program_manual')):
            return
        # TODO: Optimise this so that only items that have changed are reprogrammed by storing the last programmed values
        # For each DDS channel
            
        for i in range(MAX_NUM_CHANNELS):
            # and for each subchnl in the DDS,
            for subchnl in ['freq', 'amp', 'phase']:
                self.program_static(i, subchnl, front_panel_values['channel %d' % i][subchnl])
            # for pid_setting in ['P', 'I', 'D', 'SetPoint']:
            #     self.program_PID(i, pid_setting, PID_values['channel %d' % i][pid_setting])
        return self.check_remote_values()

    def program_static(self, channel, type, value):
        if type == 'freq':
            # print(value)
            command = 'FREQ,%d,%fMHz' % (channel + 1, value)
            self.dev.cmd(command)
        elif type == 'amp':
            # print(value)
            command = 'POW,%d,%f dBm' % (channel + 1, value)
            self.dev.cmd(command)
        elif type == 'phase':
            # print(value)
            command = 'PHASE,%d,%fdeg' % (channel + 1, value)
            self.dev.cmd(command)
        else:
            raise TypeError(type)
        # Now that a static update has been done, we'd better invalidate the saved STATIC_DATA:
        self.smart_cache['STATIC_DATA'] = None

    def transition_to_buffered(self, device_name, h5file, initial_values, fresh):
        # try to reconnect. return on failure.
        if (self.dev is None) and (not self.reconnect('check_remote_values')):
            # Andi: TODO update code as in test case without connection above!
            # each channel can be in table mode or not and in table mode can be triggered one time or each step
            # these options are given in connection table.
            # the table_data contains time/frequency/amplitude/phase for all cases.
            # time is in seconds and needs to be divided by 5us and is needed only in table mode with single trigger.
            return False

        # Store the initial values in case we have to abort and restore them:
        self.initial_values = initial_values
        print(f"'{device_name}' Transition to buffered. Device info: {self.dev.ask('info')}  ")
        # Store the final values to for use during transition_to_static:
        self.final_values = {}
        static_data = None
        table_data = None

        self.shot_file = h5file
        with h5py.File(self.shot_file, 'r') as hdf5_file:
            group = hdf5_file['/devices/' + device_name]
            for channel in range(MAX_NUM_CHANNELS):
                # If there are values to set the unbuffered outputs to, set them now:
                if 'STATIC_DATA%i'%channel in group:
                    static_data = group['STATIC_DATA%i'%channel][:]
                if 'TABLE_DATA%i'%channel in group:
                    table_data = group['TABLE_DATA%i'%channel][:]

                if table_data is not None: #Added by Andre
                    self.dev.cmd(f'MODE,{channel+1},TSB')            
                    self.dev.cmd(f'TABLE,CLEAR,{channel+1}')            
                    self.dev.cmd(F'TABLE,EDGE,{channel+1},RISING') # set trigger edge rising
                    print(f"Ch {channel} in table mode:")
                    if True:
                        data = table_data
                        for i, line in enumerate(data):
                            st = time.time()
                            # oldtable = self.smart_cache['TABLE_DATA%i'%channel]
                            ddsno = channel
                            if fresh or (line['freq'], line['phase' ], line['amp']) != 0: 
                                command = 'TABLE,APPEND,%d,%.3f,%.3f,%.3f,0x1, TRIG' % (ddsno+1, 1e-3*line['freq'], 1e-2*line['amp'], line['phase'])
                                print(f"A line in the table of Ch {ddsno} has changed sending command", command)
                                self.dev.cmd(command)

                            et = time.time()
                            tt = et - st
                            self.logger.debug('Time spent on line %s: %s' % (i, tt))
                        command = 'TABLE,APPEND,%d,10,0x0,0,0x1, TRIG' % (channel+1)
                        print(f"A line in the table of Ch {channel} has changed sending command", command)
                        self.dev.cmd(command)

                    self.dev.cmd('TABLE,ARM,%i' % (channel+1))
                    print('table armed')
                    # self.dev.cmd('TABLE,START,%i' % (channel+1))
                    # print('table started')
                    table_data = None


                elif static_data is not None: # Added by Andre
                    print(f"Ch {channel} in static mode: {static_data[-1]['freq']} MHz, {static_data[-1]['amp']} dBm")
                    
                    self.dev.cmd(f'MODE,{channel+1},NSB') 
                    self.dev.cmd(f"FREQ,{channel+1},{1e-3*static_data[-1]['freq']}") ##### BUG  TODO: FIX removing 1e-3 ask Andre #################
                    self.dev.cmd(f"POW,{channel+1},{1e-2*static_data[-1]['amp']}")   ##### BUG  TODO: FIX removing 1e-2 ask Andre #################
                    self.dev.cmd(f"PID, SETPOINT, {channel + 1}, {static_data[-1]['pid_setpoint']/1000}")

                    self.dev.cmd('ON,%i,ALL' % (channel+1))

                    # self.final_values[f'channel {channel}']['freq'] = 1e-3*static_data[-1]['freq']
                    # self.final_values[f'channel {channel}']['amp'] = 1e-2*static_data[-1]['amp']
                    # self.final_values[f'channel {channel}']['phase'] = static_data[-1]['phase']
                    # print(self.PIDstatus)
                    if self.PIDstatus[channel]:
                        self.dev.cmd('PID,ENABLE,%i, AMPL' % (channel+1))

                    ask=self.dev.ask(f'PID,STATUS,{channel+1}')
                    print(f'PID of channel {channel} is {str(ask)}')
        return self.final_values

    def abort_transition_to_buffered(self):
        return self.transition_to_manual(True)
    
    def abort_buffered(self):
        # TODO: untested
        return self.transition_to_manual(True)

    def transition_to_manual(self, abort=False):
        print('Transition to manual')
        if self.dev is not None:

            for channel in range(MAX_NUM_CHANNELS): 
                try:
                    self.dev.cmd(f'TABLE,STOP,{channel+1}') 
                    self.dev.cmd(f'TABLE,CLEAR,{channel+1}')  
                    self.dev.cmd(f'MODE,%i,NSB' % (channel+1))
                    self.dev.cmd(f"ON,{channel+1},SIG")
                    print(f"Ch {channel} end of table mode")
                except:
                    print(f"Ch {channel} already in normal mode")
                    self.dev.cmd('MODE,%i,NSB' % (channel+1))
                    self.dev.cmd(f"ON,{channel+1},SIG")
                ask=self.dev.ask(f'PID,STATUS,{channel+1}')
                print(f'PID of channel {channel} is {str(ask)}')

            if abort:
                DDSs = [] # Andi to avoid problems
                #pass
                # If we're aborting the run, then we need to reset DDSs 2 and 3 to their initial values.
                # 0 and 1 will already be in their initial values. We also need to invalidate the smart
                # programming cache for them.
                # values = self.initial_values
                # DDSs = [2,3]
                # self.smart_cache['STATIC_DATA'] = None
            else:
                # If we're not aborting the run, then we need to set DDSs 0 and 1 to their final values.
                # 2 and 3 will already be in their final values.
                values = self.final_values
                DDSs = [0, 1, 2, 3]

            # only program the channels that we need to
            # for ddsnumber in DDSs:
            #     channel_values = values['channel %d' % ddsnumber]
            #     for subchnl in ['freq', 'amp', 'phase']:
            #         self.program_static(ddsnumber, subchnl, channel_values[subchnl])

        # return True to indicate we successfully transitioned back to manual mode
        return True

    def shutdown(self):
        # Andi: execute only when we are connected
        if self.dev is not None:
            # turn both channels off
            for i in range(MAX_NUM_CHANNELS):
                self.dev.cmd('off,%d,all' % (i + 1))
            self.dev.close()

    def onSignal(self, channel, state):
        # Andi: switch RF signal on/off. returns True if ok, False on error.
        cmd = 'ON' if state else 'OFF'
        info = "'%s' channel %i: RF signal %s" % (self.device_name, channel, cmd)
        if self.dev is not None:
            self.dev.cmd('%s,%i,SIG' % (cmd, channel + 1))
            print(info)
            return True
        print(info + ' failed!')
        return False
   
    def onAmp(self, channel, state):
        # Andi: switch RF amplifier on/off. returns True if ok, False on error.
        cmd = 'ON' if state else 'OFF'
        info = "'%s' channel %i: RF amplifier %s" % (self.device_name, channel, cmd)
        if self.dev is not None:
            self.dev.cmd('%s,%i,POW' % (cmd, channel + 1))
            print(info)
            return True
        print(info + ' failed!')
        return False

    def onBoth(self, channel, state):
        # Andi: switch RF signal & amplifier on/off. returns True if ok, False on error.
        cmd = 'ON' if state else 'OFF'
        info = "'%s' channel %i: RF signal & amplifier %s" % (self.device_name, channel, cmd)
        if self.dev is not None:
            self.dev.cmd('%s,%i,ALL' % (cmd, channel + 1))
            print(info)
            return True
        print(info + ' failed!')
        return False
     
    def onPID(self, channel, state):
        # Andre: switch PID mode ENABLEd or DISABLEd. returns True if ok, False on error.
        cmd = 'ENABLE' if state else 'DISABLE'
        mod_cmd='ON' if state else 'OFF'
        info = "'%s' channel %i: amplitude PID is %sD" % (self.device_name, channel, cmd)
        if self.dev is not None:
            if state:
                self.dev.cmd('MOD, %i, AMPL, %s' % (channel + 1, mod_cmd))
                self.dev.cmd('MAPMOD, %i, %s' % (channel + 1, channel + 1))
                self.dev.cmd('PID, %s ,%i, AMPL' % (cmd, channel + 1))
            else:
                self.dev.cmd('PID, %s ,%i, AMPL' % (cmd, channel + 1))
                self.dev.cmd('MOD, %i, AMPL, %s' % (channel + 1, mod_cmd))
            self.PIDstatus[channel]=state
            print(info)
            return True
        print(info + ' failed!')
        return False
       
    def setPID(self, channel, setting, value):
        # Andre: set PID GAIN P proportional, I integral, D derivative. returns True if ok, False on error.
        info = "'%s' channel %i: PID's %s is set to %.1f %s" % (self.device_name, channel, setting, value, '%')
        if self.dev is not None:
            self.dev.cmd('PID, GAIN, %i, %s, %f' % (channel + 1, setting, value/100))
            print(info)
            return True
        print(info + ' failed!')
        return False
     
    def setpointPID(self, channel, value): #value must be [-1,+1] V
        # Andre: PID setpoint: applies a DC offset to anable locking at non-zero setpoint voltage. returns True if ok, False on error.
        info = "'%s' channel %i: PID's setpoint at %.1f mV" % (self.device_name, channel, value)
        if self.dev is not None:
            self.dev.cmd('PID, SETPOINT, %i, %f' % (channel + 1, value/1000))
            print(info)
            return True
        print(info + ' failed!')
        return False
           
    def invertPID(self, channel, state):
        # Andre: inverts the controller action. returns True if ok, False on error.
        cmd = 'ON' if state else 'OFF'
        info = "'%s' channel %i: PID is inverted to %s" % (self.device_name, channel, cmd)
        if self.dev is not None:
            print(info)
            self.dev.cmd('P, INVERT, %i' % (channel + 1))
            return True
        print(info + ' failed!')
        return False   
   
    def errorPID(self, channel):
        # Andre: returns the value of the error signal fed into the PID control loop, for diagnostic purposes
        result = self.dev.ask('PID, ERROR, %i' % (channel + 1))
        value = float(result[0:4])*1000
        print(f'error signal at: {value}') 
        return value
     
    def statusPID(self, channel):
        # Andre: report the current status of the PID controller and whether saturation occured
        return self.dev.cmd('PID, STATUS, %i' % (channel + 1)) 

    def pregainPID(self, channel, value):
        # Andre: set PID preGAIN. It returns True if ok, False on error.
        mod_type='AMPL'
        info = "'%s' channel %i: PID's %s PreGAIN is set to %i  %s" % (self.device_name, channel, mod_type, value, '%')
        if self.dev is not None:
            self.dev.cmd('GAIN, %i, %s, %f' % (channel + 1, mod_type, value)) 
            print(info)
            return True
        print(info + ' failed!')
        return False

    def print_main(self, string):
        print(string)     

@runviewer_parser
class RunviewerClass(object):
    def __init__(self, path, device):
        self.path = path
        self.name = device.name
        self.device = device

    def get_traces(self, add_trace, clock=None):
        if clock is None:
            # we're the master pseudoclock, software triggered. So we don't have to worry about trigger delays, etc
            raise Exception('No clock passed to %s. The XRF021 must be clocked by another device.'%self.name)

        times, clock_value = clock[0], clock[1]

        clock_indices = np.where((clock_value[1:]-clock_value[:-1])==1)[0]+1
        # If initial clock value is 1, then this counts as a rising edge (clock should be 0 before experiment)
        # but this is not picked up by the above code. So we insert it!
        if clock_value[0] == 1:
            clock_indices = np.insert(clock_indices, 0, 0)
        clock_ticks = times[clock_indices]

        # get the data out of the H5 file
        data = {}
        with h5py.File(self.path, 'r') as f:
            if 'TABLE_DATA' in f['devices/%s'%self.name]:
                table_data = f['devices/%s/TABLE_DATA'%self.name][:]
                for i in range(MAX_NUM_CHANNELS):
                    for sub_chnl in ['freq', 'amp', 'phase','pid_setpoint']:
                        data['channel %d_%s'%(i,sub_chnl)] = table_data['%s%d'%(sub_chnl,i)][:]

            if 'STATIC_DATA' in f['devices/%s'%self.name]:
                static_data = f['devices/%s/STATIC_DATA'%self.name][:]
                for i in range(2,4):
                    for sub_chnl in ['freq', 'amp', 'phase','pid_setpoint']:
                        data['channel %d_%s'%(i,sub_chnl)] = np.empty((len(clock_ticks),))
                        data['channel %d_%s'%(i,sub_chnl)].fill(static_data['%s%d'%(sub_chnl,i)][0])


        for channel, channel_data in data.items():
            data[channel] = (clock_ticks, channel_data)

        for channel_name, channel in self.device.child_list.items():
            for subchnl_name, subchnl in channel.child_list.items():
                connection = '%s_%s'%(channel.parent_port, subchnl.parent_port)
                if connection in data:
                    add_trace(subchnl.name, data[connection], self.name, connection)

        return {}
