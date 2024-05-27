
from labscript_devices import register_classes

register_classes(
    'SpectrumAWG',
    BLACS_tab='user_devices.SpectrumAWG.blacs_tabs.SpectrumAWGTab',
    runviewer_parser=None,
)
