from labscript import *
from labscript_devices.PulseBlasterUSB import PulseBlasterUSB
from user_devices.FPGA_device import *
import numpy as np
#import labscript as ls
#import labscript_devices.PulseBlasterUSB as pbusb

# Digital Device 
#PulseBlasterUSB(name='pulseblaster_0', board_number=0, programming_scheme='pb_start/BRANCH')

# Clockline
#ClockLine(name='pulseblaster_0_clockline', pseudoclock=pulseblaster_0.pseudoclock, connection='flag 0')

#Digital Ouput
#DigitalOut('digiout_1',pulseblaster_0.direct_outputs, 'flag 1')
#DigitalOut('digiout_2',pulseblaster_0.direct_outputs, 'flag 2')

# AnalogOut(name='anout_1', parent_device=pulseblaster_0,  connection='ao0')

################

# # Use a virtual, or 'dummy', device for the psuedoclock
# DummyPseudoclock(name='pseudoclock')

# # An output of this DummyPseudoclock is its 'clockline' attribute, which we use to trigger children devices
# DummyIntermediateDevice(name='pulseblaster_0.direct_outputs', parent_device=pulseblaster_0.pseudoclock)

# # # Create an AnalogOut child of the DummyIntermediateDevice
# AnalogOut(name='analog_out', parent_device=pulseblaster_0.direct_outputs, connection='ao0')

# FPGA device (pseudoclock device)
#       name = name string.
#       ip_address = IP address of board
#       ip_port = port number string
#       bus_rate = maximum bus output rate in MHz
#       num_racks = number of connected racks. must be 1 or 2. keep cable as short as possible, otherwise use several boards!
# each board can drive max. 2 nearby racks with independent device addresses and strobe (96bits per sample).
# if need more racks or more than few Meter distance use several boards with one as primary board, others are connected as secondary boards.
primary   = FPGA_board(name='coraboard0', ip_address='192.168.1.10', ip_port=DEFAULT_PORT, bus_rate=1.0, num_racks=1)
#secondary = FPGA_board(name='coraboard1', ip_address='192.168.1.11', ip_port=DEFAULT_PORT, bus_rate=1.0, num_racks=1)

# if True: # use secondary board
#     secondary = FPGA_board(name='coraboard1', ip_address='192.168.0.11', ip_port=DEFAULT_PORT, bus_rate=1.0, num_racks=1, trigger_device=coraboard0, trigger_connection='secondary')
# else:
#     secondary = None

# digital outputs
# DigitalChannels: (intermediate device)
#       name = name of device. give as parent_device to DigitalOut.
#       parent_device = FPGA_board object. this is name given to FPGA_board(name=...) but without quotes.
#       connection = device address string. shared by all channels. can be hex (with '0x') or decimal.
#       rack = 0 or 1
#       max_channels = maximum number of allowed channels (typically 16)
# DigitalOut: (individual output channel)
#       name = name of channel.
#       parent_device = DigitalChannels object. this is name given to DigitalChannels(name=...) but without quotes.
#       connection = unique channel number string. can be hex (with '0x') or decimal.
DigitalChannels(name='DO0', parent_device=coraboard0, connection='0x00', rack=0, max_channels = 16)
for i in range(16):
    DigitalOut(name='test'+str(i), parent_device=DO0, connection=str(i))
# if secondary:
#     DigitalChannels(name='DO1', parent_device=coraboard1, connection='0x01', rack=0, max_channels = 16)
#     for i in range(16):
#         DigitalOut(name='out'+str(i), parent_device=DO1, connection=str(i))
# else:
#     DigitalChannels(name='DO1', parent_device=coraboard0, connection='0x02', rack=0, max_channels=16)
#     for i in range(16):
#         DigitalOut(name='out' + str(i), parent_device=DO1, connection=str(i))

# analog outputs
# AnalogChannels: (intermediate device)
#       name = name of device. give as parent_device to AnalogOut.
#       parent_device = FPGA_board object. this is name given to FPGA_board(name=...) but without quotes.
#       rack = 0 or 1
#       max_channels = maximum number of allowed channels (typically 2 or 4)
# AnalogOut: (individual output channel)
#       name = name of channel.
#       parent_device = AnalogChannels object. this is name given to AnalogChannels(name=...) but without quotes.
#       connection = device address string. can be hex (with '0x') or decimal.
# AnalogChannels(name='AO0'   , parent_device=coraboard0, rack=0, max_channels = 2)
# AnalogOut     (name='coil_x', parent_device=AO0, connection='0x03' )
# AnalogOut     (name='coil_y', parent_device=AO0, connection='0x04')

# AnalogChannels(name='AO1'   , parent_device=coraboard0, rack=0, max_channels = 2)
# AnalogOut     (name='coil_z', parent_device=AO1, connection='0x15')

# AnalogChannels(name='AO2'   , parent_device=coraboard0, rack=0, max_channels = 4)
# AnalogOut     (name='HV_out', parent_device=AO2, connection='0x06',
#                unit_conversion_class=generic_conversion,
#                unit_conversion_parameters={'unit': 'kV', 'equation': 'x*10/1000'})

# if secondary:
#     AnalogChannels(name='AO3'   , parent_device=board1, rack=0, max_channels = 2)
#     AnalogOut     (name='test_x', parent_device=AO3, connection='0x03')
#     AnalogOut     (name='test_y', parent_device=AO3, connection='0x04')

if __name__ == '__main__':
    # Begin issuing labscript primitives
    # start() elicits the commencement of the shot
    start()

    # Stop the experiment shot with stop()
    stop(1.0)

