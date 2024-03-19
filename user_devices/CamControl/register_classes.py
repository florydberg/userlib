#####################################################################
#                                                                   #
# based on /labscript_devices/IMAQdxCamera/blacs_tabs.py            #
#                                                                   #
#  Andrea'simplementation of Camera_Control in labscript.suite      #
#                                                                   #
#  version of 12/01/2024                                            #
#####################################################################

from labscript_devices import register_classes

register_classes(
    'CamControl',
    BLACS_tab='user_devices.CamControl.blacs_tabs.CamControl',
    runviewer_parser=None,
)
