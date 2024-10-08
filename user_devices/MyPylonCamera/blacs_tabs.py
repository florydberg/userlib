#####################################################################
#                                                                   #
# /labscript_devices/PylonCamera/blacs_tabs.py                      #
#                                                                   #
# Copyright 2019, Monash University and contributors                #
#                                                                   #
# This file is part of labscript_devices, in the labscript suite    #
# (see http://labscriptsuite.org), and is licensed under the        #
# Simplified BSD License. See the license.txt file in the root of   #
# the project for the full license.                                 #
#                                                                   #
#####################################################################

from labscript_devices.IMAQdxCamera.blacs_tabs import IMAQdxCameraTab

class MyPylonCameraTab(IMAQdxCameraTab):
    
    # override worker class
    worker_class = 'user_devices.MyPylonCamera.blacs_workers.MyPylonCameraWorker'

