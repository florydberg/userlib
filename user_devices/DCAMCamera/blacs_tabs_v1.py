#####################################################################
#                                                                   #
# /user_devices/DCAMCamera/blacs_tabs.py                            #
#                                                                   #
# Jan 2023, Marvin Holten                                           #
#                                                                   #
#                                                                   #
#####################################################################

from labscript_devices.IMAQdxCamera.blacs_tabs import IMAQdxCameraTab
from blacs.device_base_class import (
    DeviceTab,
    define_state,
    MODE_BUFFERED,
    MODE_MANUAL,
    MODE_TRANSITION_TO_BUFFERED,
    MODE_TRANSITION_TO_MANUAL,
)

class DCAMCameraTab(IMAQdxCameraTab):
    """Thin sub-class of obj:`IMAQdxCameraTab`.
    
    This sub-class only defines :obj:`worker_class` to point to the correct
    :obj:`DCAMCameraWorker`."""
    
    # override worker class
    worker_class = 'user_devices.DCAMCamera.blacs_workers.DCAMCameraWorker'

    @define_state(
        MODE_MANUAL
        | MODE_BUFFERED
        | MODE_TRANSITION_TO_BUFFERED
        | MODE_TRANSITION_TO_MANUAL,
        True,
    )
    def status_monitor(self, notify_queue=None):

        status, clock_status, waits_pending = yield (
            self.queue_work(self.primary_worker, "check_status")
        )

        # Manual mode or aborted
        done_condition = status == 0 or status == 5

        # Update GUI status/clock status widgets
        self.status_label.setText(f"Status: {status}")
        self.clock_status_label.setText(f"Clock status: {clock_status}")

        if notify_queue is not None and done_condition and not waits_pending:
            # Experiment is over. Tell the queue manager about it, then
            # set the status checking timeout back to every 2 seconds
            # with no queue.
            notify_queue.put("done")
            self.statemachine_timeout_remove(self.status_monitor)
            self.statemachine_timeout_add(2000, self.status_monitor)

    @define_state(MODE_BUFFERED, True)
    def keep_saving(self, notify_queue):
        """ Keeps saving images rightaway in the shot dataframe without waiting for manual."""

        self.statemachine_timeout_remove(self.status_monitor)
        yield (self.queue_work(self.primary_worker, "keep_saving"))
        self.status_monitor()
        self.statemachine_timeout_add(10, self.status_monitor, notify_queue)