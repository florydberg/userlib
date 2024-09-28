from labscript import *
######################
p=0 #Pulseblaster
a=0 #AWG
f=1 #FPGA
se=0 #secondary FPGA
mb=1 #MogLabsBlue
mr=1 #MogLabsRed
ca=0 #Camera Andor
cb_abs=1 #Camera Basler for Absorption
cb_fluo=0 #Camera Basler for Fluorescence
cb_extra=0 #extra basler on the objective
co=0 #Camera Orca

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

    main_board   = FPGA_board(name='main_board',  ip_address='192.168.1.10', ip_port=DEFAULT_PORT, bus_rate=1.0, num_racks=1,
                       trigger_device=parent,
                       worker_args={'inputs': {'start trigger'  : ('input 0', 'low level')},
                                    'outputs':{'output 0':('sync out','low level')}})
    
        #to control DigiOut in script:
    # name.go_high(t) or name.ho-low(t)

    ########################                         DigiOut                               ########################
    DO0=DigitalChannels(name='DO0', parent_device=main_board, connection='0x04', rack=0, max_channels = 16)
    if not mb:
        DigitalOut(name='QRFBlue_trigger', parent_device=DO0, connection=str(0))
        DigitalOut(name='dueD_MOT_gate', parent_device=DO0, connection=str(1))
        DigitalOut(name='treD_MOT_gate', parent_device=DO0, connection=str(2))
        DigitalOut(name='ImagingBeam_gate', parent_device=DO0, connection=str(3))
        DigitalOut(name='ImagingTweezBeam_gate', parent_device=DO0, connection=str(4))

    DigitalOut(name='coilsMosfet', parent_device=DO0, connection=str(5))   
    DigitalOut(name='Tweezer_gate', parent_device=DO0, connection=str(6))
    if not co:
        DigitalOut(name='Orca_Camera_trigger', parent_device=DO0, connection=str(7))    
    if not cb_abs:
        DigitalOut(name='Basler_Camera_abs_trigger', parent_device=DO0, connection=str(8))  
    if not mr:
        DigitalOut(name='QRFRed_trigger', parent_device=DO0, connection=str(9))
        DigitalOut(name='RED_switch', parent_device=DO0, connection=str(10))
        DigitalOut(name='RedMOT_gate', parent_device=DO0, connection=str(11))
        DigitalOut(name='Free_gate', parent_device=DO0, connection=str(11))
        DigitalOut(name='Sisyphus_gate', parent_device=DO0, connection=str(11))
        
    DigitalOut(name='awg_trigger', parent_device=DO0, connection=14)
    IGBT_close=DigitalOut(name='IGBT_close', parent_device=DO0, connection=str(15))
        # RED_multifrq=DigitalOut(name='RED_multifrq', parent_device=DO0, connection=str(13))

    DO2=DigitalChannels(name='DO2'  , parent_device=main_board, connection='0x05', rack=0, max_channels = 16)

    DigitalOut(name='Red_commonSwitch', parent_device=DO2, connection=str(0))
    DigitalOut(name='Red_multiFrq', parent_device=DO2, connection=str(1))
    DigitalOut(name='Red_singleFrq', parent_device=DO2, connection=str(2))
    DigitalOut(name='Shutter_Blue', parent_device=DO2, connection=str(3))

    if not cb_fluo:
        DigitalOut(name='Basler_Camera_fluo_trigger', parent_device=DO2, connection=str(4))
    if not cb_extra:
        DigitalOut(name='Basler_Camera_extra_trigger', parent_device=DO2, connection=str(8))    
    # for i in range(5,16):
    #     DigitalOut(name='pokemon'+str(i+1), parent_device=DO2, connection=str(i))

    ########################                         Floating                               ########################
    if False:
        AnalogChannels(name='AO1', parent_device=test_board, rack=0, max_channels = 2)
        AnalogOut     (name='Gandalf', parent_device=AO1, connection='0x01')
        AnalogOut     (name='Saruman', parent_device=AO1, connection='0x02')
    ########################                         Grnd Ref                               ######################### 
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
    if False:
        DigitalChannels(name='DO1', parent_device=main_board, connection='0x05', rack=0, max_channels=16)
        for i in range(16):
            DigitalOut(name='digimon' + str(i+17), parent_device=DO1, connection=str(i))

    if se: # use secondary board
        if p:
            parent=pb0_trg
        else:
            parent=main_board
        secondary = FPGA_board(name='test_board', ip_address='192.168.1.11', ip_port=DEFAULT_PORT, bus_rate=1.0, num_racks=1, 
                           trigger_device=parent,
                           worker_args={'inputs': {'start trigger'  : ('input 0', 'low level')}}) 


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

    else:
        secondary = None
############################################################################################################### MogLabs-QRFs
if mb:
    from user_devices.MOGLabs_QRF import MOGLabs_QRF, QRF_DDS
    QRF_trigger_1=DigitalOut(name='QRFBlue_trigger', parent_device=DO0, connection=0)

    if p:
        QRF_Blue=MOGLabs_QRF(name='QRF_Blue', parent_device=pb0_trg, addr='192.168.1.102', port=7802)
    elif f:
        MOGLabs_QRF(name='QRF_Blue', parent_device=QRF_trigger_1, addr='192.168.1.102', port=7802)

    dueD_MOT=QRF_DDS(name='dueD_MOT', parent_device=QRF_Blue, connection='channel 0', 
            table_mode=False,                         digital_gate={'device':DO0, 'connection': 1})
    treD_MOT=QRF_DDS(name='treD_MOT', parent_device=QRF_Blue, connection='channel 1', 
            table_mode=False, trigger_each_step=True, digital_gate={'device':DO0, 'connection': 2})
    treD_MOT_trigger=treD_MOT_gate
    ImagingBeam=QRF_DDS(name='ImagingBeam', parent_device=QRF_Blue, connection='channel 3', 
            table_mode=False, trigger_each_step=True, digital_gate={'device':DO0, 'connection': 3})
    ImagingBeam_trigger=ImagingBeam_gate
    ImagingTweezBeam=QRF_DDS(name='ImagingTweezBeam', parent_device=QRF_Blue, connection='channel 2', 
            table_mode=False, trigger_each_step=True, digital_gate={'device':DO0, 'connection': 4})
    ImagingTweezBeam_trigger=ImagingTweezBeam_gate

if mr:
    from user_devices.MOGLabs_QRF import MOGLabs_QRF, QRF_DDS
    QRF_trigger_2=DigitalOut(name='QRFRed_trigger', parent_device=DO0, connection=9)

    if p:
        QRF_Red=MOGLabs_QRF(name='QRF_Red', parent_device=pb0_trg, addr='192.168.1.103', port=7802)
    elif f:
        QRF_Red=MOGLabs_QRF(name='QRF_Red', parent_device=QRF_trigger_2, addr='192.168.1.103', port=7802)

    BlueSpectr=QRF_DDS(name='BlueSpectr', parent_device=QRF_Red, connection='channel 0', 
            table_mode=False,                         digital_gate={'device':DO0, 'connection': 10})
    RedMOT=QRF_DDS(name='RedMOT', parent_device=QRF_Red, connection='channel 1', 
            table_mode=True, trigger_each_step=True, digital_gate={'device':DO0, 'connection': 11})
    RedMOT_trigger=RedMOT_gate
    Free=QRF_DDS(name='Free', parent_device=QRF_Red, connection='channel 2', 
            table_mode=False, trigger_each_step=True, digital_gate={'device':DO0, 'connection': 12})
    Free_trigger=Free_gate
    Sisyphus=QRF_DDS(name='Sisyphus', parent_device=QRF_Red, connection='channel 3', 
            table_mode=False, trigger_each_step=True, digital_gate={'device':DO0, 'connection': 13})

############################################################################################################### CAMERAS
if ca:
    from labscript_devices.AndorSolis.labscript_devices import AndorSolis

    Andor_Camera = AndorSolis('Andor_Camera',
            parent_device=DO0,
            serial_number=10430, 
            connection=7,
            exception_on_failed_shot=False,
            trigger_duration=0.050,
            orientation='Andor_Camera',
            camera_attributes = {
                'acquisition': 'kinetic_series',
                'emccd': False,
                'emccd_gain': 50,
                'preamp': False,
                'preamp_gain': 1.0,
                'exposure_time': 0.01, #s
                'shutter_output': 'low',
                'int_shutter_mode': 'auto',
                'ext_shutter_mode': 'auto',
                'shutter_t_open': 100,
                'shutter_t_close': 100,
                'readout': 'full_image',
                'crop': False,
                'trigger': 'external',
                'trigger_edge': 'rising',
                'number_accumulations': 1,
                'accumulation_period': 0.003,
                'number_kinetics': 1,
                'kinetics_period': 0.03,
                'xbin': 1,
                'ybin': 1,
                'center_row': None,
                'height': 1024,
                'width': 1024,
                'left_start': 1,
                'bottom_start': 1,
                'v_offset': 0,
                'acquisition_timeout': 5000.0,
                'cooldown': True,
                'water_cooling': False,
                'temperature': -60},
            manual_mode_camera_attributes = {
                # 'acquisition': 'kinetic_series',
                # 'emccd': False,
                # 'emccd_gain': 0,
                # 'preamp': False,
                # 'preamp_gain': 1.0,
                'exposure_time': 0.0000003,
                # 'shutter_output': 'low',
                # 'int_shutter_mode': 'perm_open',
                # 'ext_shutter_mode': 'auto',
                # 'shutter_t_open': 100,
                # 'shutter_t_close': 100,
                # 'readout': 'full_image',
                # 'crop': False,
                'trigger': 'internal',
                # 'trigger_edge': 'rising',
                # 'number_accumulations': 1,
                # 'accumulation_period': 0.003,
                # 'number_kinetics': 1,
                # 'kinetics_period': 0.030,
                # 'xbin': 1,
                # 'ybin': 1,
                # 'center_row': None,
                # 'height': 1024,
                # 'width': 1024,
                # 'left_start': 1,
                # 'bottom_start': 1,
                # 'v_offset': 0,
                # 'acquisition_timeout': 5000.0,
                'cooldown': True,
            #     'water_cooling': False,
                'temperature': -60}
            )

if cb_abs:
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

                'Width': 1000,
                'Height': 1000,
                'OffsetX': 1800,
                'OffsetY': 1000,
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

if cb_fluo:
    from labscript_devices.PylonCamera.labscript_devices import PylonCamera
    
    #example of use: Basler_Camera.expose(t=0.45,'exposure1')
    Basler_Camera_fluo = PylonCamera('Basler_Camera_fluo',parent_device=DO2, parentless=False, connection=4,
            serial_number=24867935,
            minimum_recovery_time=36e-3,
            trigger_duration=10,
            stop_acquisition_timeout='inf',
            exception_on_failed_shot=False,
            camera_attributes = {
                'ExposureMode': 'Timed',
                'ExposureTime':  500, #in us  >432
                'AutoExposureTimeUpperLimit':10000000,
                'AcquisitionFrameRate':29,

                'Width': 1000,
                'Height': 1000,
                'OffsetX': 1800,
                'OffsetY': 1000,
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

if co:
    from user_devices.DCAMCamera.labscript_devices  import DCAMCamera

    Orca_Camera= DCAMCamera('Orca_Camera', parent_device=DO0, #needs t=+250*ms after start before arming the trigger
                            connection=7,
                            serial_number='000548',
                            parentless=False,
                            camera_attributes = {
                                'TRIGGER GLOBAL EXPOSURE': 2.0,                                
                                'EXPOSURE TIME':0.012, # 0.0082944, #sec
                                'SENSOR MODE': 1.0,
                                'READOUT SPEED': 2.0,
                                'READOUT DIRECTION': 1.0,
                                'COLORTYPE': 1.0,
                                'BIT PER CHANNEL': 16.0,

                                'TRIGGER SOURCE': 2, #1 internal, 2 external
                                'TRIGGER MODE': 2.0,
                                'TRIGGER ACTIVE': 1.0,

                                'TRIGGER POLARITY': 2.0,
                                'TRIGGER CONNECTOR': 1.0,
                                'TRIGGER TIMES': 1.0,
                                'TRIGGER DELAY': 0.0,

                                'SENSOR TEMPERATURE': -20.0,
                                'SENSOR COOLER STATUS': 2.0,

                                'DEFECT CORRECT MODE': 2.0,
                                'HOT PIXEL CORRECT LEVEL': 1.0,
                                'BINNING': 1.0,

                                'IMAGE WIDTH': 4096.0,
                                'IMAGE HEIGHT': 2304.0,
                                'IMAGE ROWBYTES': 8192.0,
                                'IMAGE FRAMEBYTES': 18874368.0,
                                'IMAGE TOP OFFSET BYTES': 0.0,
                                'IMAGE PIXEL TYPE': 2.0,
                                'IMAGE CAMERA STAMP': 0.0,

                                'OUTPUT TRIGGER SOURCE[0]': 4.0,
                                'OUTPUT TRIGGER POLARITY[0]': 2.0,
                                'OUTPUT TRIGGER ACTIVE[0]': 1.0,
                                'OUTPUT TRIGGER DELAY[0]': 0.0,
                                'OUTPUT TRIGGER PERIOD[0]': 0.0009999999999999998,
                                'OUTPUT TRIGGER KIND[0]': 2.0,
                                
                                'OUTPUT TRIGGER PRE HSYNC COUNT': 0.0,

                                # 'SUBARRAY HPOS': 0.0,
                                # 'SUBARRAY HSIZE': 4096.0,
                                # 'SUBARRAY VPOS': 0.0,
                                # 'SUBARRAY VSIZE': 2304.0,
                                # 'SUBARRAY MODE': 1.0,

                                'CAPTURE MODE': 1.0, #must stay 1
                                'INTENSITY LUT MODE': 1.0,
                                'INTENSITY LUT PAGE': 1.0,

                                # 'INTERNAL LINE SPEED': 0.638888888888889,
                                # 'INTERNAL LINE INTERVAL': 7.2e-06,

                                # 'RECORD FIXED BYTES PER FILE': 256.0,
                                # 'RECORD FIXED BYTES PER SESSION': 916.0,
                                # 'RECORD FIXED BYTES PER FRAME': 18874416.0,

                                # 'MASTER PULSE MODE': 1.0,
                                # 'MASTER PULSE TRIGGER SOURCE': 1.0,
                                # 'MASTER PULSE INTERVAL': 0.1,
                                # 'MASTER PULSE BURST TIMES': 1.0,

                                # 'SYSTEM ALIVE': 2.0,
                                # 'CONVERSION FACTOR COEFF': 0.11,
                                # 'CONVERSION FACTOR OFFSET': 200.0,
                            },
                            
                            manual_mode_camera_attributes = {
                                'TRIGGER SOURCE': 1, #1 internal, 2 external
                                # 'TRIGGER MODE': 2.0,
                            },
                            ) # ref file:///C:/Users/florydberg01/Documents/Orca-settings/propC15550-20UP_en.html
       
############################################################################################################### AWG
if a:
    from user_devices.SpectrumAWG.labscript_devices import SpectrumAWG, AWGOutput

    # # Create the AWG device
    awg = SpectrumAWG('awg', device_path="/dev/spcm0", timeout=5000, channel_mode='single', sample_rate=1250e6)
    Vertical=AWGOutput("Vertical", awg, "0", main_board, 'ext0', 2000)
    # Horizontal=AWGOutput("Horizontal", awg, "1", main_board, 'ext0', 2000)
    # AWGOutput("Horizontal", awg, "1", None, None, 100)
#################################################################################
 # ATTENTION: start() and stop(1) cannot be missing! time for stop must be >0. #
#################################################################################

if __name__ == '__main__':
    start()
    t=0
    dt=main_board.time_step #1mu second
    Shutter_Blue.go_low(t)
    # Andor_Camera.enable_cooldown(temperature_setpoint=-60, water_cooling=False, wait_until_stable=False)
    if mb:
        from user_devices.mogdevice import MOGDevice  #Blue MOGLABS QRF
        dev = MOGDevice('192.168.1.102')
        print('Device info:', dev.ask('info'))

        dev.cmd('MODE,1,  NSB') #2D MOT
        dev.cmd('FREQ,1,198.0')
        dev.cmd('POW, 1, 28')

        dev.cmd('MODE,2,  NSB') #3D MOT
        dev.cmd('FREQ,2,169.0')
        dev.cmd('POW, 2, 28')

        dev.cmd('MODE,3,  NSB') #TwezImaging
        dev.cmd('FREQ,3,111.0')
        dev.cmd('POW, 3, 26.86')

        dev.cmd('MODE,4,  NSB') #Imaging
        dev.cmd('FREQ,4,113')
        dev.cmd('POW, 4, 20')


        # RedMOT.DDS.setfreq(tt, G_Red_MOT_Frq)
        # RedMOT.DDS.setamp(tt, G_Red_MOT_Pow)

        # ImagingBeam.DDS.setfreq(tt, G_Imaging_Frq)
        # ImagingBeam.DDS.setamp(tt, G_Imaging_Pow)

        # dueD_MOT.DDS.setfreq(tt, G_dueD_MOT_Frq)
        # dueD_MOT.DDS.setamp(tt, G_dueD_MOT_Pow)

        # treD_MOT.DDS.setfreq(tt, G_treD_MOT_Frq)
        # treD_MOT.DDS.setamp(tt, G_treD_MOT_Pow)

        # ImagingTweezBeam.DDS.setfreq(tt, G_ImagingTweez_Frq)
        # ImagingTweezBeam.DDS.setamp(tt, G_ImagingTweez_Pow)

    if mr:
        from user_devices.mogdevice import MOGDevice  #Red MOGLABS QRF
        dev = MOGDevice('192.168.1.103')
        print('Device info:', dev.ask('info'))

        dev.cmd('MODE,1,  NSB')
        dev.cmd('FREQ,1,110.3')
        dev.cmd('POW, 1, 27.2')

        dev.cmd('MODE,2,  NSB')
        dev.cmd('FREQ,2, 70.0')
        dev.cmd('POW, 2, 24.0')

        dev.cmd('MODE,3,  NSB')
        dev.cmd('FREQ,3, 80.0')
        dev.cmd('POW, 3, 29.0')

        dev.cmd('MODE,4,  NSB')
        dev.cmd('FREQ,4, 80.0')
        dev.cmd('POW, 4, 29.1')

    stop(t+dt)