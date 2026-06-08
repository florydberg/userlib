#####################################################################
#                                                                   #
# /user_devices/DCAMCamera/blacs_tabs.py                            #
#                                                                   #
# Jan 2023, Marvin Holten                                           #
#                                                                   #
#                                                                   #
#####################################################################

from labscript_devices.IMAQdxCamera.blacs_tabs import IMAQdxCameraTab
from blacs.tab_base_classes import Worker, define_state, MODE_MANUAL, MODE_TRANSITION_TO_BUFFERED, MODE_TRANSITION_TO_MANUAL, MODE_BUFFERED

class DCAMCameraTab(IMAQdxCameraTab):
    """Thin sub-class of obj:`IMAQdxCameraTab`.
    
    This sub-class only defines :obj:`worker_class` to point to the correct
    :obj:`DCAMCameraWorker`."""
    
    # override worker class
    worker_class = 'user_devices.DCAMCamera.blacs_workers.DCAMCameraWorker'

    @define_state(MODE_BUFFERED, True)
    def keep_save(self, notify_queue):
        print('status monitor (FPGA)')
        result = yield(self.queue_work(self.primary_worker, 'keep_save'))
        if result[0]: # end or error
            # indicate that experiment cycle is finished.
            # this causes transition_to_manual called on all workers.
            notify_queue.put('done')
            # do not call status_monitor anymore
            self.statemachine_timeout_remove(self.keep_save)