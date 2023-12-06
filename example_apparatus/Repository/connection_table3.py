from labscript import *
# import time
# from user_devices.generic_conversion import generic_conversion

################################################################################################################# PULSE
a=1
if a: # PulseBlaster as parent device (is False make sure board0 has None trigger_device)
    from labscript_devices.PulseBlasterESRPro500 import PulseBlasterESRPro500
    from labscript_devices import PulseBlaster

    pb0 = PulseBlasterESRPro500(name='pulseblaster_0', board_number=0, programming_scheme='pb_start/BRANCH')
    Trigger(name='pb0_trg', parent_device=pb0.direct_outputs, connection='flag 20', trigger_edge_type='rising')
    Trigger(name='cam_trg', parent_device=pb0.direct_outputs, connection= 'flag 19', trigger_edge_type='rising')
    Trigger(name='mog_trg', parent_device=pb0.direct_outputs, connection= 'flag 18', trigger_edge_type='rising')
    

    # Clockline
    ClockLine(name='pulseblaster_0_clockline', pseudoclock=pulseblaster_0.pseudoclock, connection='flag 0')

    #Digital Ouput
    DigitalOut('digiout_1',pulseblaster_0.direct_outputs, 'flag 1')
    DigitalOut('digiout_2',pulseblaster_0.direct_outputs, 'flag 2')
else:
    pb0_trg = None

############################################################################################################### ANDOR
b=1
if b:
    from labscript_devices.AndorSolis.labscript_devices import AndorSolis
 
    RemoteBLACS('test_remote', 'localhost')
    AndorSolis(
        'camera',
        cam_trg,
        'trigger',
        serial_number=10430,#0xDEADBEEF
        worker=test_remote,
        mock=True,
    )

############################################################################################################### AWG
d=0
if d:
    from user_devices.SpectrumAWG import SpectrumAWG
    import lascar

    # Create the AWG device
    # awg_connection = lascar.awg.Connect()
    awg = SpectrumAWG('awg', parent_device=None, connection=pb0_trg)


############################################################################################################### FPGA
e=1
if e:
    from user_devices.FPGA_device import FPGA_board, DigitalChannels, AnalogChannels, DEFAULT_PORT
    
    primary   = FPGA_board(name='board0',  ip_address='192.168.1.10', ip_port=DEFAULT_PORT, bus_rate=1.0, num_racks=1,
                       trigger_device=pb0_trg,
                       worker_args={'inputs': {'NOP bit' : ('data bits 28-31', 'offset bit 3'),
                                               'STRB bit': ('data bits 20-23', 'offset bit 3'),
                                               'start trigger'  : ('input 0', 'rising edge')},
                                    'outputs':{'output 0':('sync out','high level')}})

    if True: # use secondary board
        secondary = FPGA_board(name='board1', ip_address='192.168.1.11', ip_port=DEFAULT_PORT, bus_rate=1.0, num_racks=1, 
                           trigger_device=pb0_trg,
                           worker_args={'inputs': {'NOP bit'        : ('data bits 28-31','offset bit 3'),
                                                   'STRB bit'       : ('data bits 20-23','offset bit 3'),
                                                   'start trigger'  : ('input 0', 'rising edge')}}) 
    else:
        secondary = None
else:
    primary = None

if primary is not None:
    ########################                         DigiOut                               ########################
    DigitalChannels(name='DO0'  , parent_device=board0, connection='0x04', rack=0, max_channels = 16)
    for i in range(16):
        DigitalOut(name='digimon'+str(i+1), parent_device=DO0, connection=str(i))

    if True:
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
    AnalogChannels(name='AO0'   , parent_device=board0, rack=0, max_channels = 6)
    AnalogOut     (name='Freezer', parent_device=AO0, connection='0x08' )
    AnalogOut     (name='Cell', parent_device=AO0, connection='0x09')
    AnalogOut     (name='Majinbu', parent_device=AO0, connection='0x0A')
    AnalogOut     (name='Cooler', parent_device=AO0, connection='0x0B')
    if secondary:
        AnalogChannels(name='AO2'   , parent_device=board1, rack=0, max_channels = 4)
        AnalogOut     (name='Goku', parent_device=AO2, connection='0x08' )
        AnalogOut     (name='Vegeta', parent_device=AO2, connection='0x09')
        AnalogOut     (name='Junior', parent_device=AO2, connection='0x0A')
        AnalogOut     (name='Gohan', parent_device=AO2, connection='0x0B')

        AnalogChannels(name='AO3'   , parent_device=board1, rack=0, max_channels = 4)
        AnalogOut     (name='Rufy', parent_device=AO3, connection='0x18' )
        AnalogOut     (name='Zoro', parent_device=AO3, connection='0x19')
        AnalogOut     (name='Sanji', parent_device=AO3, connection='0x1A')
        AnalogOut     (name='Nami', parent_device=AO3, connection='0x1B')

        AnalogChannels(name='AO4'   , parent_device=board1, rack=0, max_channels = 4)
        AnalogOut     (name='Lupin', parent_device=AO4, connection='0x20' )
        AnalogOut     (name='Gigen', parent_device=AO4, connection='0x21')
        AnalogOut     (name='Gemon', parent_device=AO4, connection='0x22')
        AnalogOut     (name='Zenigata', parent_device=AO4, connection='0x23')
############################################################################################################## Quad RF
c=0
if c:# MOGLABS Quad RF synthesizer. give primary board or pulseblaster as parent_device 

    from user_devices.MOGLabs_QRF import MOGLabs_QRF, QRF_DDS
    # from labscript_devices.MOGLabs_XRF021 import MOGLabs_XRF021, MOGDevice

    # MOGLABS Quad RF synthesizer. give primary board as parent_device
    MOGLabs_QRF(name='QFR_0', parent_device=pb0, addr='qrf', port=7802)

    DDS(name='test_DDS_0',parent_device=QFR_0,connection='channel 0')
    DDS(name='test_DDS_1',parent_device=QFR_0,connection='channel 1')
    DDS(name='test_DDS_2',parent_device=QFR_0,connection='channel 2')
    DDS(name='test_DDS_3',parent_device=QFR_0,connection='channel 3')

##############################################################################################################
# ATTENTION: start() and stop(1) cannot be missing! time for stop must be >0. 
##############################################################################################################
# from labscript import start, stop
if __name__ == '__main__':
    start()
    stop(1)