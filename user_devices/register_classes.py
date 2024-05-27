#####################################################################
#####################################################################
from labscript_devices import register_classes

blacs_tab = 'user_devices.FPGA_device.FPGA_Tab'
runviewer_parser = 'user_devices.FPGA_device.RunviewerClass'
register_classes(
    'FPGA_board',
    BLACS_tab=blacs_tab,
    runviewer_parser=runviewer_parser,
)

register_classes(
    'AnalogChannels',
    BLACS_tab=blacs_tab,
    runviewer_parser=runviewer_parser,
)

register_classes(
    'DigitalChannels',
    BLACS_tab=blacs_tab,
    runviewer_parser=runviewer_parser,
)

register_classes(
    'MOGLabs_QRF',
    BLACS_tab='user_devices.MOGLabs_QRF.MOGLabs_QRF_Tab',
    #runviewer_parser=runviewer_parser,
)

# register_classes(
#     'SpectrumAWG',
#     BLACS_tab='user_devices.SpectrumAWG.SpectrumAWG_Tab',
#     #runviewer_parser=runviewer_parser,
# )

# register_classes(
#     'MOG_QRF',
#     BLACS_tab='user_devices.MOG_QRF.MOG_QRF_Tab',
#     #runviewer_parser=runviewer_parser,
# )