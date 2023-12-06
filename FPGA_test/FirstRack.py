from labscript import start, stop
from labscript_utils import import_or_reload
import_or_reload('labscriptlib.FPGA_test.connection_table')
from labscriptlib.FPGA_test.connection_table import *

primary   = FPGA_board(name='board0', ip_address='192.168.1.10', ip_port=DEFAULT_PORT, bus_rate=1.0, num_racks=1,
                       worker_args={'inputs': {'NOP bit' : ('data bits 28-31', 'offset bit 3'),
                                               'STRB bit': ('data bits 20-23', 'offset bit 3')}})
if True: # use secondary board
    secondary = FPGA_board(name='board1', ip_address='192.168.1.11', ip_port=DEFAULT_PORT, bus_rate=1.0, num_racks=1, trigger_device=board0,
                           worker_args={'inputs': {'NOP bit'        : ('data bits 28-31','offset bit 3'),
                                                   'STRB bit'       : ('data bits 20-23','offset bit 3'),
                                                   'start trigger'  : ('input 0', 'falling edge')}}) 

DigitalChannels(name='DO0'  , parent_device=board0, connection='0x04', rack=0, max_channels = 16)
for i in range(16):
    DigitalOut(name='digimon'+str(i), parent_device=DO0, connection=str(i))

if secondary: 
    DigitalChannels(name='DO1'  , parent_device=board1, connection='0x05', rack=0, max_channels = 16)
    for i in range(16):
        DigitalOut(name='pokemon'+str(i), parent_device=DO1, connection=str(i))

AnalogChannels(name='AO0'   , parent_device=board0, rack=0, max_channels = 4)
AnalogOut     (name='Freezer', parent_device=AO0, connection='0x08')
AnalogOut     (name='Cell', parent_device=AO0, connection='0x09')
AnalogOut     (name='Majinbu', parent_device=AO0, connection='0x0A')
AnalogOut     (name='Cooler', parent_device=AO0, connection='0x0B')


if secondary:
    AnalogChannels(name='AO1'   , parent_device=board1, rack=0, max_channels = 4)
    AnalogOut     (name='Goku', parent_device=AO1, connection='0x08')
    AnalogOut     (name='Vegeta', parent_device=AO1, connection='0x09')
    AnalogOut     (name='Junior', parent_device=AO1, connection='0x0A')
    AnalogOut     (name='Gohan', parent_device=AO1, connection='0x0B')

from labscript import start, stop
if __name__ == '__main__':
    start()
    stop(1)