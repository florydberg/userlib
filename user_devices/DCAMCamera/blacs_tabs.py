#####################################################################
#                                                                   #
# /user_devices/DCAMCamera/blacs_tabs.py                            #
#                                                                   #
# Jan 2023, Marvin Holten                                           #
#                                                                   #
#                                                                   #
#####################################################################

from labscript_devices.IMAQdxCamera.blacs_tabs import IMAQdxCameraTab

class DCAMCameraTab(IMAQdxCameraTab):
    """Thin sub-class of obj:`IMAQdxCameraTab`.
    
    This sub-class only defines :obj:`worker_class` to point to the correct
    :obj:`DCAMCameraWorker`."""
    
    # override worker class
    worker_class = 'user_devices.DCAMCamera.blacs_workers.DCAMCameraWorker'