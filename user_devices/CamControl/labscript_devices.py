#####################################################################
#                                                                   #
# based on /labscript_devices/IMAQdxCamera/blacs_tabs.py            #
#                                                                   #
#  Andrea's implementation of Camera_Control in labscript.suite     #
#                                                                   #
#  version of 12/01/2024                                            #
#####################################################################
import sys
from labscript_utils import dedent
from labscript import TriggerableDevice, set_passed_properties
import numpy as np
import labscript_utils.h5_lock
import h5py
from user_devices.camera import Camera
from user_devices.thorlabs_tsi_sdk.tl_camera import TLCameraSDK

class ThorCam(Camera):
    """
    Thorlabs camera.

    Attributes
    ----------
    sdk : TLCameraSDK
        Object to talk with the Thorlabs SDK. Shared among instances of :class:`ThorCam`.
    cam : ThorCam
        Object to talk with the desired camera.
    profile : {'free', 'single', 'single_hardware'} or None
        Current operation mode.\n
        'free' means always capturing.\n
        'single' means only gets frame on command.\n
        'single_hardware' means only gets frame on hardware trigger or command.\n
        None means camera is disarmed.
    """

    sdk = None

    ### Initialization and termination ###

    def __init__(self, serial="", verbose=True, **kwargs):
        """
        Initialize camera and attributes. Initial profile is ``"single"``.

        Parameters
        ----------
        serial : str
            Serial number of the camera to open. If empty, defaults to the first camera in the list
            returned by :meth:`TLCameraSDK.discover_available_cameras()`.
        verbose : bool
            Whether or not to print extra information.
        kwargs
            See :meth:`.Camera.__init__` for permissible options.

        Raises
        ------
        RuntimeError
           If the camera can not be reached.
        """
        if ThorCam.sdk is None:
            if verbose:
                print("TLCameraSDK initializing... ", end="")
            try:
                ThorCam.sdk = TLCameraSDK()
            except:
                print("failure")
                raise RuntimeError(
                    "thorlabs.py: TLCameraSDK() open failed. "
                    "Is thorlabs_tsi_sdk installed? "
                    "Are the .dlls in the directory added by configure_tlcam_dll_path? "
                    "Sometimes adding the .dlls to the working directory can help."
                )
            if verbose:
                print("success")

        if verbose:
            print("Looking for cameras... ", end="")
        camera_list = ThorCam.sdk.discover_available_cameras()
        if verbose:
            print("success")

        if serial == "":
            if len(camera_list) == 0:
                raise RuntimeError("No cameras found by TLCameraSDK.")
            serial = camera_list[0]
        elif serial not in camera_list:
            raise RuntimeError(
                "Serial " + serial + " not found by TLCameraSDK. Availible: ",
                camera_list,
            )

        if verbose:
            print("ThorCam sn \"{}\" initializing... ".format(serial), end="")
        self.cam = ThorCam.sdk.open_camera(serial)

        self.cam.is_led_on = False

        # Initialize profile variable, then set to the proper value.
        self.profile = None
        self.setup("single")

        # Initialize binning to 1.
        self.set_binning()

        super().__init__(
            self.cam.image_width_pixels,
            self.cam.image_height_pixels,
            bitdepth=self.cam.bit_depth,
            dx_um=self.cam.sensor_pixel_width_um,
            dy_um=self.cam.sensor_pixel_height_um,
            name=serial,
            **kwargs
        )

        if verbose:
            print("success")

    def close(self, close_sdk=False):
        """
        See :meth:`.Camera.close`.

        Parameters
        ----------
        close_sdk : bool
            Whether or not to close the TLCameraSDK instance.
        """
        # Future: the proper way to treat sdk deletion would be
        # to keep a class-wide count of the number of open instances
        # and delete the sdk when the last instance is closed.
        # We would want to use a lock to do this.

        self.cam.dispose()

        if close_sdk:
            self.close_sdk()

    @staticmethod
    def info(verbose=True):
        """
        Discovers all Thorlabs scientific cameras.

        Parameters
        ----------
        verbose : bool
            Whether to print the discovered information.

        Returns
        --------
        list of str
            List of ThorCam serial numbers.
        """
        if ThorCam.sdk is None:
            try:
                ThorCam.sdk = TLCameraSDK()
            except:
                raise RuntimeError(
                    "thorlabs.py: TLCameraSDK() open failed. "
                    "Is thorlabs_tsi_sdk installed? "
                    "Are the .dlls in the directory added by configure_tlcam_dll_path? "
                    "Sometimes adding the .dlls to the working directory can help."
                )
            close_sdk = True
        else:
            close_sdk = False

        camera_list = ThorCam.sdk.discover_available_cameras()

        if verbose:
            print("ThorCam serials:")
            for serial in camera_list:
                print("\"{}\"".format(serial))

        if close_sdk:
            ThorCam.close_sdk()

        return camera_list

    @staticmethod
    def close_sdk():
        """
        Close the TLCameraSDK instance.
        """
        ThorCam.sdk.dispose()
        ThorCam.sdk = None

    def reset(self):
        """See :meth:`.Camera.reset`."""
        self.close()
        self.__init__()

    ### Property Configuration ###

    def get_exposure(self):
        """See :meth:`.Camera.get_exposure`."""
        return float(self.cam.exposure_time_us) / 1e6

    def set_exposure(self, exposure_s):
        """See :meth:`.Camera.set_exposure`."""
        self.cam.exposure_time_us = int(exposure_s * 1e6)

    def set_binning(self, bx=None, by=None):
        """
        Set the binning of the camera. Will error if a certain binning is not supported.

        Parameters
        ----------
        bx : int
            The binning value in the horizontal direction.
        by : int
            The binning value in the vertical direction.
        """
        # Save old profile and disarm
        profile = self.profile
        self.setup(None)

        if bx is None:
            bx = 1
        if by is None:
            by = 1
        self.cam.binx = int(bx)
        self.cam.biny = int(by)

        # Restore profile
        self.setup(profile)

    def set_woi(self, woi=None):
        """See :meth:`.Camera.set_woi`."""
        # Save old profile and disarm
        profile = self.profile
        self.setup(None)

        if woi is None:  # Default to maximum WOI
            woi = (
                self.cam.roi_range.upper_left_x_pixels_min,
                self.cam.roi_range.lower_right_x_pixels_max
                - self.cam.roi_range.upper_left_x_pixels_min + 1,
                self.cam.roi_range.upper_left_y_pixels_min,
                self.cam.roi_range.lower_right_y_pixels_max
                - self.cam.roi_range.upper_left_y_pixels_min + 1,
            )

        self.woi = woi

        newroi = ROI(
            self.cam.roi_range.lower_right_x_pixels_max - woi[0] - woi[1] + 1,
            woi[2],
            self.cam.roi_range.lower_right_x_pixels_max - woi[0],
            woi[2] + woi[3] - 1,
        )

        assert (
            self.cam.roi_range.upper_left_x_pixels_min
            <= newroi.upper_left_x_pixels
            <= self.cam.roi_range.upper_left_x_pixels_max
        )
        assert (
            self.cam.roi_range.upper_left_y_pixels_min
            <= newroi.upper_left_y_pixels
            <= self.cam.roi_range.upper_left_y_pixels_max
        )
        assert (
            self.cam.roi_range.lower_right_x_pixels_min
            <= newroi.lower_right_x_pixels
            <= self.cam.roi_range.lower_right_x_pixels_max
        )
        assert (
            self.cam.roi_range.lower_right_y_pixels_min
            <= newroi.lower_right_y_pixels
            <= self.cam.roi_range.lower_right_y_pixels_max
        )

        # Update the woi
        self.cam.roi = newroi
        self.woi = woi

        # Update the shape (test the transform; maybe make this more efficient in the future)
        test = np.zeros((woi[3], woi[1]))
        self.shape = np.shape(self.transform(test))

        # Restore profile
        self.setup(profile)

        return woi

    def setup(self, profile):
        """
        Set operation mode.

        Parameters
        ----------
        profile
            See :attr:`profile`.
        """
        if profile != self.profile:
            if profile is None:
                self.cam.disarm()
            elif profile == "free":
                self.cam.disarm()
                self.cam.frames_per_trigger_zero_for_unlimited = 0
                self.cam.operation_mode = 0  # Software triggered
                self.cam.arm(2)
                self.cam.issue_software_trigger()
            elif profile == "single":
                self.cam.disarm()
                self.cam.frames_per_trigger_zero_for_unlimited = 1
                self.cam.operation_mode = 0  # Software triggered
                self.cam.arm(2)
            elif profile == "single_hardware":
                self.cam.disarm()
                self.cam.frames_per_trigger_zero_for_unlimited = 1
                self.cam.operation_mode = 1  # Hardware triggered
                self.cam.arm(2)
            else:
                raise ValueError("Profile {} not recognized".format(profile))

            self.profile = profile

    def get_image(self, timeout_s=.1, trigger=True, grab=True, attempts=1):
        """
        See :meth:`.Camera.get_image`. By default ``trigger=True`` and ``grab=True`` which
        will result in blocking image acquisition.
        For non-blocking acquisition,
        set ``trigger=True`` and ``grab=False`` to issue a software trigger;
        then, call the method again with ``trigger=False`` and ``grab=True``
        to grab the resulting frame.

        Parameters
        ----------
        trigger : bool
            Whether or not to issue a software trigger.
        grab : bool
            Whether or not to grab the frame (blocking).

        Returns
        -------
        numpy.ndarray or None
            Array of shape :attr:`shape` if ``grab=True``, else ``None``.
        """
        should_trigger = trigger and self.profile == "single"

        for _ in range(attempts):
            if should_trigger:
                t = time.time()
                self.cam.issue_software_trigger()

            ret = None
            if grab:
                # Start the timer.
                if not should_trigger:
                    t = time.time()

                frame = None

                # Try to grab a frame until we succeed.
                while time.time() - t < timeout_s and frame is None:
                    frame = self.cam.get_pending_frame_or_null()

                ret = self.transform(np.copy(frame.image_buffer)) if frame is not None else None

                if ret is not None:
                    break

        return ret

    def flush(self, timeout_s=1, verbose=False):
        """
        See :meth:`.Camera.flush`.

        Parameters
        ----------
        verbose : bool
            Whether or not to print extra information.
        """
        # Start the timer.
        t = time.perf_counter()

        ii = 0
        frame = self.cam.get_pending_frame_or_null()
        frametime = 0

        # Continue flushing frames while the timeout is not exceeded, the
        # returned frame is empty (None), or the frame returned super fast
        # (cached)
        while (
            time.perf_counter() - t < timeout_s
            and frame is not None
            and frametime < 0.003
        ):
            t2 = time.perf_counter()
            frame = self.cam.get_pending_frame_or_null()
            frametime = time.perf_counter() - t2
            ii += 1

        if verbose:
            print(
                "Flushed {} frames in {:.2f} ms".format(
                    ii, 1e3 * (time.perf_counter() - t)
                )
            )

    def is_capturing(self):
        """
        Determine whether or not the camera is currently capturing images.

        Returns
        -------
        bool
            Whether or not the camera is actively capturing images.
        """
        return self.profile == "free"

class CamControl(TriggerableDevice):
    description = 'Cam-Control'

    @set_passed_properties(
        property_names={
            "connection_table_properties": [
                "serial_number",
                "orientation",
                "pixel_size",
                "magnification",
                "manual_mode_camera_attributes",
                "mock",
            ],
            "device_properties": [
                "camera_attributes",
                "stop_acquisition_timeout",
                "exception_on_failed_shot",
                "saved_attribute_visibility_level"
            ],
        }
    )
    def __init__(
        self,
        name,
        parent_device,
        connection,
        serial_number,
        orientation=None,
        pixel_size=[1.0,1.0],
        magnification=1.0,
        trigger_edge_type='rising',
        trigger_duration=None,
        minimum_recovery_time=0.0,
        camera_attributes=None,
        manual_mode_camera_attributes=None,
        stop_acquisition_timeout=5.0,
        exception_on_failed_shot=True,
        saved_attribute_visibility_level='intermediate',
        mock=False,
        **kwargs
    ):

        self.trigger_edge_type = trigger_edge_type
        self.minimum_recovery_time = minimum_recovery_time
        self.trigger_duration = trigger_duration
        self.orientation = orientation
        self.pixel_size = pixel_size
        self.magnification = magnification
        if isinstance(serial_number, (str, bytes)):
            serial_number = int(serial_number, 16)
        self.serial_number = serial_number
        self.BLACS_connection = hex(self.serial_number)[2:].upper()
        if camera_attributes is None:
            camera_attributes = {}
        if manual_mode_camera_attributes is None:
            manual_mode_camera_attributes = {}
        for attr_name in manual_mode_camera_attributes:
            if attr_name not in camera_attributes:
                msg = f"""attribute '{attr_name}' is present in
                    manual_mode_camera_attributes but not in camera_attributes.
                    Attributes that are to differ between manual mode and buffered
                    mode must be present in both dictionaries."""
                raise ValueError(dedent(msg))
        valid_attr_levels = ('simple', 'intermediate', 'advanced', None)
        if saved_attribute_visibility_level not in valid_attr_levels:
            msg = "saved_attribute_visibility_level must be one of %s"
            raise ValueError(msg % valid_attr_levels)
        self.camera_attributes = camera_attributes
        self.manual_mode_camera_attributes = manual_mode_camera_attributes
        self.exposures = []
        TriggerableDevice.__init__(self, name, parent_device, connection, **kwargs)

    def expose(self, t, name, frametype='frame', trigger_duration=None):

        # Backward compatibility with code that calls expose with name as the first
        # argument and t as the second argument:
        if isinstance(t, str) and isinstance(name, (int, float)):
            msg = """expose() takes `t` as the first argument and `name` as the second
                argument, but was called with a string as the first argument and a
                number as the second. Swapping arguments for compatibility, but you are
                advised to modify your code to the correct argument order."""
            print(dedent(msg), file=sys.stderr)
            t, name = name, t
        if trigger_duration is None:
            trigger_duration = self.trigger_duration
        if trigger_duration is None:
            msg = """%s %s has not had an trigger_duration set as an instantiation
                argument, and none was specified for this exposure"""
            raise ValueError(dedent(msg) % (self.description, self.name))
        if not trigger_duration > 0:
            msg = "trigger_duration must be > 0, not %s" % str(trigger_duration)
            raise ValueError(msg)
        self.trigger(t, trigger_duration)
        self.exposures.append((t, name, frametype, trigger_duration))
        return trigger_duration

    def generate_code(self, hdf5_file):
        self.do_checks()
        vlenstr = h5py.special_dtype(vlen=str)
        table_dtypes = [
            ('t', float),
            ('name', vlenstr),
            ('frametype', vlenstr),
            ('trigger_duration', float),
        ]
        data = np.array(self.exposures, dtype=table_dtypes)
        group = self.init_device_group(hdf5_file)
        if self.exposures:
            group.create_dataset('EXPOSURES', data=data)
