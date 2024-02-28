from labscript import *
#######################

p=0 #Pulseblaster
a=0 #AWG
f=1 #FPGA
se=0 #secondary FPGA
mb=0 #MogLabsBlue
mr=1 #MogLabsRed
ca=0 #Camera Andor
cb=1 #Camera Basler
ct=0 #Camera Thorlabs

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

############################################################################################################### AWG
if a:
    from user_devices.SpectrumAWG import SpectrumAWG
    import lascar

    # Create the AWG device
    # awg_connection = lascar.awg.Connect()
    awg = SpectrumAWG('awg', parent_device=awg_trigger, connection='trigger')

############################################################################################################### FPGA  
if f:
    if p:
        from user_devices.FPGA_device import FPGA_board, DigitalChannels, AnalogChannels, DEFAULT_PORT
        parent=pb0_trg
    else:
        from user_devices.FPGA_device_Alone import FPGA_board, DigitalChannels, AnalogChannels, DEFAULT_PORT
        parent=None

    primary   = FPGA_board(name='main_board',  ip_address='192.168.1.10', ip_port=DEFAULT_PORT, bus_rate=1.0, num_racks=1,
                       trigger_device=parent,
                       worker_args={'inputs': {'start trigger'  : ('input 0', 'low level')},
                                    'outputs':{'output 0':('sync out','low level')}})

    if se: # use secondary board
        if p:
            parent=pb0_trg
        else:
            parent=primary
        secondary = FPGA_board(name='test_board', ip_address='192.168.1.11', ip_port=DEFAULT_PORT, bus_rate=1.0, num_racks=1, 
                           trigger_device=parent,
                           worker_args={'inputs': {'start trigger'  : ('input 0', 'low level')}}) 
    else:
        secondary = None

if f: #outputs
    #to control DigiOut in script:
    # name.go_high(t) or name.ho-low(t)

    ########################                         DigiOut                               ########################
    DO0=DigitalChannels(name='DO0', parent_device=primary, connection='0x04', rack=0, max_channels = 16)
    if not mb:
        DigitalOut(name='QRFBlue_trigger', parent_device=DO0, connection=str(0))
        DigitalOut(name='dueD_MOT_gate', parent_device=DO0, connection=str(1))
        DigitalOut(name='treD_MOT_gate', parent_device=DO0, connection=str(2))
        DigitalOut(name='ImagingBeam_gate', parent_device=DO0, connection=str(3))
        DigitalOut(name='ImagingTweezBeam_gate', parent_device=DO0, connection=str(4))

    DigitalOut(name='COILS_switch', parent_device=DO0, connection=str(5))   
    DigitalOut(name='Tweezer_gate', parent_device=DO0, connection=str(6))
    # DigitalOut(name='CameraAndor_trg', parent_device=DO0, connection=str(7))
    if not cb:
        DigitalOut(name='Basler_Camera_trigger', parent_device=DO0, connection=str(8))  

    if not mr:
        DigitalOut(name='QRFRed_trigger', parent_device=DO0, connection=str(9))
        DigitalOut(name='BlueSpectr_gate', parent_device=DO0, connection=str(10))
        DigitalOut(name='RedMOT_gate', parent_device=DO0, connection=str(11))
        DigitalOut(name='Free_gate', parent_device=DO0, connection=str(12))
        DigitalOut(name='Sisyphus_gate', parent_device=DO0, connection=str(13))
    DigitalOut(name='digimon15', parent_device=DO0, connection=14)
    Cam_trg=DigitalOut(name='CameraZelux_trg', parent_device=DO0, connection=15)

    if False:
        DigitalChannels(name='DO1', parent_device=primary, connection='0x05', rack=0, max_channels=16)
        for i in range(16):
            DigitalOut(name='digimon' + str(i+17), parent_device=DO1, connection=str(i))

    if secondary: 
        DigitalChannels(name='DO2'  , parent_device=test_board, connection='0x04', rack=0, max_channels = 16)
        for i in range(16):
            DigitalOut(name='pokemon'+str(i+1), parent_device=DO2, connection=str(i))

    ########################                         Floating                               ########################
    if False:
        AnalogChannels(name='AO1', parent_device=test_board, rack=0, max_channels = 2)
        AnalogOut     (name='Gandalf', parent_device=AO1, connection='0x01')
        AnalogOut     (name='Saruman', parent_device=AO1, connection='0x02')
    ########################                         Grnd Ref                               ######################### 
    AnalogChannels(name='AO0'   , parent_device=main_board, rack=0, max_channels = 4)
    AnalogOut     (name='COILS_current1', parent_device=AO0, connection='0x08')
    AnalogOut     (name='COILScomp_current1', parent_device=AO0, connection='0x09')
    AnalogOut     (name='COILScomp_current2', parent_device=AO0, connection='0x0A')
    AnalogOut     (name='COILScomp_current3', parent_device=AO0, connection='0x0B')
    if secondary:
        AnalogChannels(name='AO2'   , parent_device=test_board, rack=0, max_channels = 4)
        AnalogOut     (name='Goku', parent_device=AO2, connection='0x08')
        AnalogOut     (name='Vegeta', parent_device=AO2, connection='0x09')
        AnalogOut     (name='Junior', parent_device=AO2, connection='0x0A')
        AnalogOut     (name='Gohan', parent_device=AO2, connection='0x0B')

        AnalogChannels(name='AO3'   , parent_device=test_board, rack=0, max_channels = 4)
        AnalogOut     (name='Rufy', parent_device=AO3, connection='0x18')
        AnalogOut     (name='Zoro', parent_device=AO3, connection='0x19')
        AnalogOut     (name='Sanji', parent_device=AO3, connection='0x1A')
        AnalogOut     (name='Nami', parent_device=AO3, connection='0x1B')

        AnalogChannels(name='AO4'   , parent_device=test_board, rack=0, max_channels = 4)
        AnalogOut     (name='Lupin', parent_device=AO4, connection='0x20')
        AnalogOut     (name='Gigen', parent_device=AO4, connection='0x21')
        AnalogOut     (name='Gemon', parent_device=AO4, connection='0x22')
        AnalogOut     (name='Zenigata', parent_device=AO4, connection='0x23')
############################################################################################################### MogLabs-QRFs

if mb:
    from user_devices.MOGLabs_QRF import MOGLabs_QRF, QRF_DDS
    QRF_trigger_1=DigitalOut(name='QRFBlue_trigger', parent_device=DO0, connection=0)

    if p:
        MOGLabs_QRF(name='QRF_Blue', parent_device=pb0_trg, addr='192.168.1.102', port=7802)
    elif f:
        MOGLabs_QRF(name='QRF_Blue', parent_device=QRF_trigger_1, addr='192.168.1.102', port=7802)

    QRF_DDS(name='dueD_MOT', parent_device=QRF_Blue, connection='channel 0', 
            table_mode=False,                         digital_gate={'device':DO0, 'connection': 1})
    QRF_DDS(name='treD_MOT', parent_device=QRF_Blue, connection='channel 1', 
            table_mode=True, trigger_each_step=False, digital_gate={'device':DO0, 'connection': 2})
    QRF_DDS(name='ImagingBeam', parent_device=QRF_Blue, connection='channel 2', 
            table_mode=True, trigger_each_step=True, digital_gate={'device':DO0, 'connection': 3})
    QRF_DDS(name='ImagingTweezBeam', parent_device=QRF_Blue, connection='channel 3', 
            table_mode=True, trigger_each_step=True, digital_gate={'device':DO0, 'connection': 4})

if mr:
    from user_devices.MOGLabs_QRF import MOGLabs_QRF, QRF_DDS
    QRF_trigger_2=DigitalOut(name='QRFRed_trigger', parent_device=DO0, connection=9)

    if p:
        MOGLabs_QRF(name='QRF_Red', parent_device=pb0_trg, addr='192.168.1.103', port=7802)
    elif f:
        MOGLabs_QRF(name='QRF_Red', parent_device=QRF_trigger_2, addr='192.168.1.103', port=7802)

    QRF_DDS(name='BlueSpectr', parent_device=QRF_Red, connection='channel 0', 
            table_mode=False,                         digital_gate={'device':DO0, 'connection': 10})
    QRF_DDS(name='Red_MOT', parent_device=QRF_Red, connection='channel 1', 
            table_mode=True, trigger_each_step=False, digital_gate={'device':DO0, 'connection': 11})
    QRF_DDS(name='Free', parent_device=QRF_Red, connection='channel 2', 
            table_mode=True, trigger_each_step=True, digital_gate={'device':DO0, 'connection': 12})
    QRF_DDS(name='Sisyphus', parent_device=QRF_Red, connection='channel 3', 
            table_mode=True, trigger_each_step=True, digital_gate={'device':DO0, 'connection': 13})

#to control moglabs in script in NSB (normale triggerable mode):
    # dev.cmd('ARG', channel, new_valu)
    # where ARG can be FREQ, POW, PHASE

############################################################################################################### CAMERAS
if ca:
    from labscript_devices.AndorSolis.labscript_devices import AndorSolis

    Andor_Camera = AndorSolis('Andor_Camera',parent_device=DO0, parentless=True, connection=7,
        serial_number=str(10430))

if cb:
    from labscript_devices.PylonCamera.labscript_devices import PylonCamera
    
    #example of use: Basler_Camera.expose(t=0.45,'exposure1')
    Basler_Camera = PylonCamera('Basler_Camera',parent_device=DO0, parentless=False, connection=8,
            serial_number=24799497,
            minimum_recovery_time=36e-3,
            trigger_duration=10,
            stop_acquisition_timeout='inf',
            exception_on_failed_shot=False,
            camera_attributes = {
                'ExposureMode': 'Timed',
                'ExposureTime':  500000, #in us  >432
                'AutoExposureTimeUpperLimit':10000000,
                'AcquisitionFrameRate':29,

                'Width': 600,
                'Height': 600,
                'OffsetX': 2000,
                'OffsetY': 1200,
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

                'Gain': 0,
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
    
if ct:
    from user_devices.CamControl.labscript_devices import ThorCam
#################################################################################
 # ATTENTION: start() and stop(1) cannot be missing! time for stop must be >0. #
#################################################################################

if __name__ == '__main__':
    start()
    t=0
    dt=main_board.time_step #1mu second
    if mb:
        from user_devices.mogdevice import MOGDevice  #Blue MOGLABS QRF
        dev = MOGDevice('192.168.1.102')
        print('Device info:', dev.ask('info'))

        dev.cmd('MODE,1,  NSB')
        dev.cmd('FREQ,1,200.0')
        dev.cmd('POW, 1, 29.1')

        dev.cmd('MODE,2,  NSB')
        dev.cmd('FREQ,2,180.0')
        dev.cmd('POW, 2, 29.1')

        dev.cmd('MODE,3,  NSB')
        dev.cmd('FREQ,3,114.0')
        dev.cmd('POW, 3, 26.0')

        dev.cmd('MODE,4,  NSB')
        dev.cmd('FREQ,1,114.0')
        dev.cmd('POW, 1, 26.0')

    if mr:
        from user_devices.mogdevice import MOGDevice  #Red MOGLABS QRF
        dev = MOGDevice('192.168.1.103')
        print('Device info:', dev.ask('info'))

        dev.cmd('MODE,1,  NSB')
        dev.cmd('FREQ,1,114.0')
        dev.cmd('POW, 1, 27.2')

        dev.cmd('MODE,2,  NSB')
        dev.cmd('FREQ,2, 80.0')
        dev.cmd('POW, 2, 29.1')

        dev.cmd('MODE,3,  NSB')
        dev.cmd('FREQ,3, 80.0')
        dev.cmd('POW, 3, 29.0')

        dev.cmd('MODE,4,  NSB')
        dev.cmd('FREQ,1, 80.0')
        dev.cmd('POW, 1, 29.1')

    stop(t+dt)