from labscript import *
#######################
p=0 #Pulseblaster
f=1 #FPGA
se=0 #secondary FPGA
m=0 #Moglabs
c=0 #Camera
a=0 #AWG
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
    primary   = FPGA_board(name='board0',  ip_address='192.168.1.10', ip_port=DEFAULT_PORT, bus_rate=1.0, num_racks=1,
                       trigger_device=parent,
                       worker_args={'inputs': {'start trigger'  : ('input 0', 'low level')},
                                    'outputs':{'output 0':('sync out','low level')}})

    if se: # use secondary board
        if p:
            parent=pb0_trg
        else:
            parent=primary
        secondary = FPGA_board(name='board1', ip_address='192.168.1.11', ip_port=DEFAULT_PORT, bus_rate=1.0, num_racks=1, 
                           trigger_device=parent,
                           worker_args={'inputs': {'start trigger'  : ('input 0', 'low level')}}) 
    else:
        secondary = None
else:
    primary = None

if f: #output
    ########################                         DigiOut                               ########################
    DO0=DigitalChannels(name='DO0', parent_device=primary, connection='0x04', rack=0, max_channels = 16)
    if not m:
        DigitalOut(name='QRF_trigger', parent_device=DO0, connection=str(0))
        DigitalOut(name='dueD_MOT_gate', parent_device=DO0, connection=str(1))
        DigitalOut(name='treD_MOT_gate', parent_device=DO0, connection=str(2))
        DigitalOut(name='ImagingBeam_gate', parent_device=DO0, connection=str(3))
        DigitalOut(name='TweezImag_gate', parent_device=DO0, connection=str(4))
    DigitalOut(name='Tweezer_gate', parent_device=DO0, connection=str(6))

    DigitalOut(name='COILS_switch', parent_device=DO0, connection=str(5))   

    DigitalOut(name='Basler_trg', parent_device=DO0, connection=str(7))   
    for i in range(8,15):
        DigitalOut(name='digimon'+str(i+1), parent_device=DO0, connection=str(i))  
    Cam_trg=DigitalOut(name='Cam_trg', parent_device=DO0, connection=str(15))

    if False:
        DigitalChannels(name='DO1', parent_device=board0, connection='0x05', rack=0, max_channels=16)
        for i in range(16):
            DigitalOut(name='digimon' + str(i+17), parent_device=DO1, connection=str(i))

    if secondary: 
        DigitalChannels(name='DO2'  , parent_device=board1, connection='0x04', rack=0, max_channels = 16)
        for i in range(16):
            DigitalOut(name='pokemon'+str(i+1), parent_device=DO2, connection=str(i))

    ########################                         Floating                               ########################
    if False:
        AnalogChannels(name='AO1', parent_device=board1, rack=0, max_channels = 2)
        AnalogOut     (name='Gandalf', parent_device=AO1, connection='0x01')
        AnalogOut     (name='Saruman', parent_device=AO1, connection='0x02')
    ########################                         Grnd Ref                               ######################### 
    AnalogChannels(name='AO0'   , parent_device=board0, rack=0, max_channels = 4)
    AnalogOut     (name='COILS_current1', parent_device=AO0, connection='0x08')
    AnalogOut     (name='COILS_current2', parent_device=AO0, connection='0x09')
    AnalogOut     (name='ANDOR', parent_device=AO0, connection='0x0A')
    AnalogOut     (name='Freezer', parent_device=AO0, connection='0x0B')
    if secondary:
        AnalogChannels(name='AO2'   , parent_device=board1, rack=0, max_channels = 4)
        AnalogOut     (name='Goku', parent_device=AO2, connection='0x08')
        AnalogOut     (name='Vegeta', parent_device=AO2, connection='0x09')
        AnalogOut     (name='Junior', parent_device=AO2, connection='0x0A')
        AnalogOut     (name='Gohan', parent_device=AO2, connection='0x0B')

        AnalogChannels(name='AO3'   , parent_device=board1, rack=0, max_channels = 4)
        AnalogOut     (name='Rufy', parent_device=AO3, connection='0x18')
        AnalogOut     (name='Zoro', parent_device=AO3, connection='0x19')
        AnalogOut     (name='Sanji', parent_device=AO3, connection='0x1A')
        AnalogOut     (name='Nami', parent_device=AO3, connection='0x1B')

        AnalogChannels(name='AO4'   , parent_device=board1, rack=0, max_channels = 4)
        AnalogOut     (name='Lupin', parent_device=AO4, connection='0x20')
        AnalogOut     (name='Gigen', parent_device=AO4, connection='0x21')
        AnalogOut     (name='Gemon', parent_device=AO4, connection='0x22')
        AnalogOut     (name='Zenigata', parent_device=AO4, connection='0x23')
############################################################################################################### Mogs-QRF

if m:
    from user_devices.MOGLabs_QRF import MOGLabs_QRF, QRF_DDS
    # from user_devices.MOG_QRF import MOG_QRF, MOGDevice

    QRF_trigger_1=DigitalOut(name='QRF_trigger', parent_device=DO0, connection=0)

    if p:
        MOGLabs_QRF(name='QRF_MOT', parent_device=pb0_trg, addr='192.168.1.102', port=7802)
    elif f:
        MOGLabs_QRF(name='QRF_MOT', parent_device=QRF_trigger_1, addr='192.168.1.102', port=7802)

    QRF_DDS(name='dueD_MOT', parent_device=QRF_MOT, connection='channel 0', 
            table_mode=False,                         digital_gate={'device':DO0, 'connection': 1})
    QRF_DDS(name='treD_MOT', parent_device=QRF_MOT, connection='channel 1', 
            table_mode=True, trigger_each_step=False, digital_gate={'device':DO0, 'connection': 2})
    # QRF_DDS(name='ImagingBeam', parent_device=QRF_MOT, connection='channel 2', 
    #         table_mode=True, trigger_each_step=True, digital_gate={'device':DO0, 'connection': 3})
#     QRF_DDS(name='TwezImaging', parent_device=QRF_MOT, connection='channel 3', 
#             table_mode=True, trigger_each_step=True, digital_gate={'device':DO0, 'connection': 4})

############################################################################################################### CAMERAS
if c:
    from labscript_devices.PylonCamera.labscript_devices import PylonCamera
    from labscript_devices.AndorSolis.labscript_devices import AndorSolis

    RemoteBLACS('test_remote', 'localhost')
    AndorSolis(
        'camera',
        Cam_trg,
        'trigger',
        serial_number= 10430,# 0x28BE, #'X-10430',
        # worker=test_remote,
        # mock=True,
    )
    # PCam=PylonCamera(
    #     'camera',
    #     Cam_trg,
    #     'trigger',
    #     serial_number= 10430,# 0x28BE, #'X-10430',
    #     # worker=test_remote,
    #     # mock=True,
    # )

#################################################################################
 # ATTENTION: start() and stop(1) cannot be missing! time for stop must be >0. #
#################################################################################

if __name__ == '__main__':
    start()
    t=0
    dt=board0.time_step #1mu second
    if True: #MoGLABS QRF
        from user_devices.mogdevice import MOGDevice
        dev = MOGDevice('192.168.1.102')
        print('Device info:', dev.ask('info'))

        t=+2*dt
        dev.cmd('MODE,1,TSB')
        dev.cmd('TABLE,CLEAR,1')
        dev.cmd('MODE,2,TSB')
        dev.cmd('TABLE,CLEAR,2')
        # dev.cmd('MODE,3,TSB')
        # dev.cmd('TABLE,CLEAR,3')
        # dev.cmd('MODE,4,TSB')
        # dev.cmd('TABLE,CLEAR,3')

        dev.cmd('TABLE,APPEND,1,200.0,29.1,0,1')
        dev.cmd('TABLE,APPEND,2,180.0,29.1,0,1')
        # dev.cmd('TABLE,APPEND,3,114.0,30.0,0,1')
        # dev.cmd('TABLE,APPEND,4,218.0,29.1,0,1')

        dev.cmd('TABLE,START,1')
        dev.cmd('TABLE,START,2')
        # dev.cmd('TABLE,START,3')
        # dev.cmd('TABLE,START,4')

    if True:
        COILS_current1.constant(t,0)
        t+=dt
        COILS_current2.constant(t,0)
        t+=dt
        ANDOR.constant(t, 0)
        t+=dt
        dueD_MOT_gate.go_high(t)
        treD_MOT_gate.go_high(t)
        # ImagingBeam_gate.go_high(t)
        COILS_switch.go_low(t)

    stop(t)