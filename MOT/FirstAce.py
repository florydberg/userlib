from labscript import start, stop
from generate_samples import generate_digital_samples, generate_analog_samples, test_word
from labscript_utils import import_or_reload
import_or_reload('labscriptlib.MOT.connection_table')

from labscriptlib.MOT.connection_table import *

import numpy
from pypylon import pylon
import pylablib as pll
pll.par["devices/dlls/basler_pylon"] = "path/to/dlls"
from pylablib.devices import Basler

camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
camera.Open()

camera.TriggerSelector.SetValue("FrameBurstStart")
camera.TriggerSource.SetValue("Line3")
camera.TriggerMode.SetValue("Off")
camera.TriggerSelector.SetValue("FrameStart")
camera.TriggerSource.SetValue("Line3")
camera.TriggerMode.SetValue("Off")

Images = []
NumberOfPictures = 3
Imagenum = 0  ### track image number


t=0
start()

camera.StartGrabbing()
t+=1

for Imagenum in range(NumberOfPictures):

    digimon7.go_high(t)
    ###  A timeout of 20 s is used.
    t+=ddelay
    grabResult = camera.RetrieveResult(20000, pylon.TimeoutHandling_ThrowException)
    Images.append(grabResult)
    t+=1
    digimon7.go_low(t)



camera.StopGrabbing()
camera.Close()


stop(t)

