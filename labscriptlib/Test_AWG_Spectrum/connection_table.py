from labscript import *
######################
p=0 #Pulseblaster
a=1 #AWG
f=1 #FPGA
cb=0 #Camera Basler for test

############################################################################################################### PULSE
if p:
    from labscript_devices.PulseBlasterESRPro500 import PulseBlasterESRPro500
    from labscript_devices import PulseBlaster

    pb0 = PulseBlasterESRPro500(name='pulseblaster_0', board_number=0, programming_scheme='pb_start/BRANCH')
    Trigger(name='pb0_trg', parent_device=pb0.direct_outputs, connection='flag 7', trigger_edge_type='rising')
    Trigger(name='cam_trg', parent_device=pb0.direct_outputs, connection= 'flag 22', trigger_edge_type='rising')
    Trigger(name='mog_trg', parent_device=pb0.direct_outputs, connection= 'flag 21', trigger_edge_type='rising')
    Trigger(name='awg_trigger', parent_device=pb0.direct_outputs, connection= 'flag 20', trigger_edge_type='rising')
    
    # Clockline
    CL=ClockLine(name='pulseblaster_0_clockline', pseudoclock=pulseblaster_0.pseudoclock, connection='flag 0')

    #Digital Ouput
    DigitalOut('digiout_1',pulseblaster_0.direct_outputs, 'flag 1')
    DigitalOut('digiout_2',pulseblaster_0.direct_outputs, 'flag 2')
############################################################################################################### FPGA  
if f:
    from user_devices.FPGA_device import FPGA_board, DigitalChannels, AnalogChannels, DEFAULT_PORT
    if p: 
        parent=pb0_trg
    else:
        parent=None

    main_board   = FPGA_board(name='main_board',  ip_address='192.168.1.11', ip_port=DEFAULT_PORT, bus_rate=1.0, num_racks=1,
                       trigger_device=parent,
                       worker_args={'inputs': {'start trigger'  : ('input 0', 'low level')},
                                      'outputs':{'output 0':('sync out','low level')}})
    
        #to control DigiOut in script:
    # name.go_high(t) or name.ho-low(t)

    ########################                         DigiOut                               ########################
    DO0=DigitalChannels(name='DO0', parent_device=main_board, connection='0x04', rack=0, max_channels = 16)
    awg_trigger=DigitalOut(name='awg_trigger', parent_device=DO0, connection=str(0))
    if cb:
        trigger_basler = DigitalOut(name='Basler_Camera_trigger', parent_device=DO0, connection=str(1))
    else:
        DigitalOut(name='dio_2', parent_device=DO0, connection=str(1))
    for i in range(2,14):
        DigitalOut(name='dio_'+str(i+1), parent_device=DO0, connection=str(i))
    Reordering_end=DigitalOut(name='Reordering_end', parent_device=DO0, connection=str(15))

    ########################                         Floating                               ########################
    if False:
        AnalogChannels(name='AO1', parent_device=test_board, rack=0, max_channels = 2)
        AnalogOut     (name='Gandalf', parent_device=AO1, connection='0x01')
        AnalogOut     (name='Saruman', parent_device=AO1, connection='0x02')
    ########################                         Grnd Ref                               ######################### 
    if False:
        AO0=AnalogChannels(name='AO0'   , parent_device=main_board, rack=0, max_channels = 4)
        AnalogOut     (name='BigCoilsI', parent_device=AO0, connection='0x08')
        AnalogOut     (name='CompCoilsI_X', parent_device=AO0, connection='0x09')
        AnalogOut     (name='CompCoilsI_Y', parent_device=AO0, connection='0x0A')
        AnalogOut     (name='CompCoilsI_Z', parent_device=AO0, connection='0x0B')

        AO1=AnalogChannels(name='AO1'   , parent_device=main_board, rack=0, max_channels = 4)
        AnalogOut     (name='BigCoilsV', parent_device=AO1, connection='0x18')
        AnalogOut     (name='Pippo', parent_device=AO1, connection='0x19')
        AnalogOut     (name='Franco', parent_device=AO1, connection='0x1A')
        AnalogOut     (name='Zio', parent_device=AO1, connection='0x1B')

############################################################################################################### CAMERAS
if cb:
    from labscript_devices.PylonCamera.labscript_devices import PylonCamera
    
    #example of use: Basler_Camera.expose(t=0.45,'exposure1')
    Basler_Camera_abs = PylonCamera('Basler_Camera_abs',parent_device=DO0, parentless=False, connection=8,
            serial_number=24799497,
            minimum_recovery_time=36e-3,
            trigger_duration=10,
            stop_acquisition_timeout=10,
            exception_on_failed_shot=False,
            camera_attributes = {
                'ExposureMode': 'Timed',
                'ExposureTime':  500, #in us  >432
                'AutoExposureTimeUpperLimit':10000000,
                'AcquisitionFrameRate':29,

                'Width': 1400,
                'Height': 1400,
                'OffsetX': 1700,
                'OffsetY': 800,
                'CenterX': False,
                'CenterY': False,
                'PixelFormat': 'Mono12',

                # 'TriggerSelector':'FrameStart',
                'TriggerMode': 'On',
                'TriggerSource':'Line3',
                # 'timeoutMs':1,
                # 'timeoutHandling':0,
            

                'LineSelector':"Line4",
                'LineMode':"Output",
                'LineSource':"ExposureActive",

                'Gain': 6,
                'ShutterMode':'GlobalResetRelease',
                'BslLightControlTriggerMode':"FlashWindow"


            #     'AcquisitionFrameRateEnable': False,
            #     'AcquisitionFrameRate': 28.99979700142099,
            #     'DeviceLinkThroughputLimitMode': 'On',
            #     'DeviceLinkThroughputLimit': 360000000,
            },

             manual_mode_camera_attributes = {
                'TriggerSource':'Software',
                'TriggerMode':'Off'
            },

            )   

############################################################################################################### AWG
if a:
    from user_devices.SpectrumAWG.labscript_devices import SpectrumAWG, AWGOutput, AWG_IO

    # # Create the AWG device
    Awg_sampleRate=1.25e9
    awg = SpectrumAWG('awg', device_path="/dev/spcm0", timeout=5000, generation_mode='sequence', memory_segments=200, sample_rate=Awg_sampleRate)
    Vertical=AWGOutput("Vertical", awg, "0", main_board, trigger_connection= 'awg_trigger', channel_amplitude = 2000)
    Horizontal=AWGOutput("Horizontal", awg, "1", main_board, trigger_connection = 'awg_trigger', channel_amplitude = 2000)
    # awg_end_flag = Trigger('awg_end_flag', awg, 'X0')  # X0 = multipurpose I/O line

############################################################################################################### AWG
if False:
    WaitMonitor(
        'reordering_wait_monitor',  # Name of the monitor
        parent_device = main_board,   # Parent device for the monitor
        connection = 'clockline',          # Connection for the monitor
        # trigger_type='falling',       # Trigger type for the monitor
        # Triggering the monitor on the 'waiting' signal
        acquisition_device = main_board,  # Device that acquires the monitor
        acquisition_connection = 'trigger',  # Connection that acquires the monitor

        # trigger_device=awg,  # Device that triggers the monitor
        # trigger_connection='X0',  # Connection that triggers the monitor
        # Optional: specify a timeout device and connection
        # timeout_device=None, timeout_connection=None, timeout_trigger_type='rising'
    )
#################################################################################
 # ATTENTION: start() and stop(1) cannot be missing! time for stop must be >0. #
#################################################################################

if __name__ == '__main__':
    start()
    t=0
    dt=main_board.time_step #1mu second

    stop(t+dt)