from user_devices.mogdevice import MOGDevice
import numpy as np
# connect to the device
dev = MOGDevice('192.168.1.102')
# construct the pulse
N = 250 # number of points to generate
X = np.linspace(-1,1,N)
P = 5 - 35*X**2 # Gaussian amplitude, =30 to +10dBm
F = 100 + 50*X # linear sweep, 50 to 150 MHz

dev.cmd('MODE,1,TSB') # set CH1 into table mode
dev.cmd('TABLE,CLEAR,1') # clear existing table

# for (f,p) in zip(F,P): # upload the entries
#     dev.cmd('TABLE,APPEND,1,%.2f,%.2f,0,1'%(f,p))
#     dev.cmd('TABLE,START,1') # execute the table