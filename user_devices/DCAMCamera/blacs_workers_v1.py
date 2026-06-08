#####################################################################
#                                                                   #
# /user_devices/DCAMCamera/blacs_workers.py                         #
#                                                                   #
# Jan 2023, Marvin Holten                                           #
#                                                                   #
# Sep 2024, Andrea Fantini                                          #
#####################################################################

from labscript_devices.IMAQdxCamera.blacs_workers import IMAQdxCameraWorker
import datetime
from labscript_utils.shared_drive import path_to_local
from labscript_utils.properties import set_attributes
import labscript_utils.properties
import h5py
from labscript_utils import dedent
import sys
import numpy as np
import threading


take_and_save=True

# Don't import API yet so as not to throw an error, allow worker to run as a dummy
# device, or for subclasses to import this module to inherit classes without requiring API
dcamAPI = None

class DCAM_Camera(object):
    """The backend hardware interface class for the DCAMCamera.
    
    This class handles all of the API/hardware implementation details for the
    corresponding labscript device. It is used by the BLACS worker to send
    appropriate API commands to the camera for the standard BLACS camera operations
    (i.e. transition_to_buffered, get_attributes, snap, etc).
    
    Attributes:
        propList (dict): Dictionary with property names and keys.
        timeout (int): Timeout in ms
        camera (dcamAPI.Dcam): Handle to connected camera.
        _abort_acquisition (bool): Abort flag that is polled during buffered
            acquisitions.
    """
    #Dictionary with all available properties names and their property IDs
    propList = {}

    def __init__(self, serial_number):
        """Initialize DCAM API camera.
        
        Searches all cameras reachable by the host using the provided serial
        number. Fails with API error if camera not found.
        
        This function also does a significant amount of default configuration.

        Args:
            serial_number (int): serial number of camera to connect to
        """
        self.timeout = 240000

        global dcamAPI
        import user_devices.DCAMCamera.dcam as dcamAPI

        print('Initialize DCAM API ...')
        if dcamAPI.Dcamapi.init() is False:
            msg = 'Dcamapi.init() fails with error {}'.format(dcamAPI.DCAMERR(dcamAPI.Dcamapi.lasterr()).name)
            dcamAPI.Dcamapi.uninit()
            raise RuntimeError(msg)

        print(f'Connecting to S/N: {serial_number:06x} ...')
        #Iterate Trough Cameras
        for camID in range(dcamAPI.Dcamapi.get_devicecount()):
            self.camera = dcamAPI.Dcam(camID)
            if self.camera.dev_open() is False:
                 print('Dcam.open() fails with error {}'.format(dcamAPI.DCAMERR(dcamAPI.Dcamapi.lasterr()).name))
                 self.camera.dev_close()
            else:
                if serial_number==int((self.camera.dev_getstring(dcamAPI.DCAM_IDSTR.CAMERAID)).split(' ')[1],16):
                    print("Correct camera found!")
                    break
                else:
                    #Not the camera we are looking for. Continue searching.
                    self.camera.dev_close()

        if serial_number!=int((self.camera.dev_getstring(dcamAPI.DCAM_IDSTR.CAMERAID)).split(' ')[1],16):
            msg = """ERROR: Camera with the selected serial number could not be found."""
            self.camera.dev_close()
            raise RuntimeError(msg)

        print("Connected to Camera: ", end='\t')
        print(self.camera.dev_getstring(dcamAPI.DCAM_IDSTR.MODEL),end='\t')
        print(self.camera.dev_getstring(dcamAPI.DCAM_IDSTR.CAMERAID))

        # Get dictionary of props
        propID = self.camera.prop_getnextid(0)
        while propID is not False:
            propAttr = self.camera.prop_getattr(propID)
            if propAttr.is_readable():
                name=self.camera.prop_getname(propID)
                self.propList[name]=propID
            propID = self.camera.prop_getnextid(propID)

        self._abort_acquisition = False
        self.exception_on_failed_shot = True

    def set_attributes(self, attr_dict):
        """Sets all attribues in attr_dict.          
        Args:
            attr_dict (dict): dictionary of property dictionaries to set for the camera.
        """
        for attr, value in attr_dict.items():
            propID = self.propList[attr]
            self.camera.prop_setvalue(propID,value)
            print("Set Attribute: ", attr ," with ID: ", propID, " to value: ", value)
        
    def get_attributes(self, visibility_level, writeable_only=True):
        """Return a nested dict of all readable attributes.
        
        Args:
            visibility_level (str): Not used.
            writeable_only (:obj:`bool`, optional): Not used
            
        Returns:
            dict: Dictionary of properties
        """
        
        props = {}
        for (name, propID) in self.propList.items():
            props[name]=self.camera.prop_getvalue(propID)
        return props

    def get_attribute(self, name):
        """Return current values dictionary of attribute of the given name.
        
        Args:
            name (str): Property name to read
            
        Returns:
            dict: Dictionary of property values with structure as defined in
                :obj:`set_attribute`.
        """
        try:
            prop_dict = {}
            propID = dcamAPI.DCAM_IDPROP.__getattr__(name).value
            value = self.camera.prop_getvalue(propID)
            prop_dict[name] = value
            return prop_dict
        except Exception as e:
            # Add some info to the exception:
            raise Exception(f"Failed to get attribute {name}") from e

    def snap(self):
        """Acquire a single image and return it
        
        Returns:
            numpy.array: Acquired image
        """
        self.configure_acquisition(continuous=False,bufferCount=1)
        self.camera.cap_snapshot()

        if self.camera.wait_capevent_frameready(self.timeout) is not False:
                image = self.camera.buf_getlastframedata()
        else:
            dcamerr = dcamAPI.Dcamapi.lasterr()
            if dcamerr.is_timeout():
                print('===: timeout')
            else:
                msg='Dcam.wait() fails with error {}'.format(dcamAPI.DCAMERR(dcamerr).name)
                raise RuntimeError(msg)
        self.camera.cap_stop()  #Andre's implementation#otherwise cannot realease buffer
        self.camera.buf_release()

        return image

    def configure_acquisition(self, continuous=True, bufferCount=10):
        """Configure acquisition buffer count and grab mode.
        
        
        Args:
            continuous (:obj:`bool`, optional): If True, camera will continuously
                acquire and only keep most recent frames in the buffer. If False,
                all acquired frames are kept and error occurs if buffer is exceeded.
                Default is True.
            bufferCount (:obj:`int`, optional): Number of memory buffers to use 
                in the acquistion. Default is 10.
        """

        print("Configuring acquisition of ", bufferCount, " images in mode ", end='')
        print("continuous.") if continuous else print("single.")
        if self.camera.buf_alloc(bufferCount) is False:
            msg='Dcam.buf_alloc() fails with error {}'.format(dcamAPI.DCAMERR(dcamAPI.Dcamapi.lasterr()).name)
            raise RuntimeError(msg)

        # Start acquisition
        # if continuous or bufferCount>1:  # Andre: why?
        self.camera.cap_start()
          
    def grab(self,bufferNo=-1):
        """Grab and return single image during pre-configured acquisition.
        
        Args:
            bufferNo (int): number of image in buffer. 
                If bufferNo=-1 (default), the function call of 
                buf_getframedata() is equal to buf_getlastframedata()

        Returns:
            numpy.array: Returns formatted image
        """
        if self.camera.wait_capevent_frameready(self.timeout):
            image = self.camera.buf_getframedata(bufferNo)
        else:
            dcamerr = dcamAPI.Dcamapi.lasterr()
            if dcamerr.is_timeout():
                raise RuntimeError('===: timeout')
            else:
                msg='Dcam.wait() fails with error {}'.format(dcamAPI.DCAMERR(dcamerr).name)
                raise RuntimeError(msg)
                
        return image

    def grab_multiple(self, n_images, images):
        """Grab n_images into images array during buffered acquistion.
        
        Grab method involves a continuous loop with fast timeout in order to
        poll :obj:`_abort_acquisition` for a signal to abort.
        
        Args:
            n_images (int): Number of images to acquire. Should be same number
                as the bufferCount in :obj:`configure_acquisition`.
            images (list): List that images will be saved to as they are acquired
        """
        print(f"Attempting to grab {n_images} images.")
        for i in range(n_images):
            if self._abort_acquisition:
                print("Abort during acquisition.")
                self._abort_acquisition = False
                return
            images.append(self.grab(bufferNo=i))

            print(f"Got image {i+1} of {n_images}.")                    

        print(f"Got {len(images)} of {n_images} images.")
        return images

    def stop_acquisition(self):
        """Tells camera to stop current acquistion."""
        print("Stop acquisition.")
        self.camera.cap_stop()
        self.camera.buf_release()

    def abort_acquisition(self):
        """Sets :obj:`_abort_acquisition` flag to break buffered acquisition loop."""
        self._abort_acquisition = True

    def close(self):
        """Closes :obj:`camera` handle to the camera."""
        self.camera.dev_close()
        dcamAPI.Dcamapi.uninit()

class DCAMCameraWorker(IMAQdxCameraWorker):
    """DCAMCameraWorker API Camera Worker. 
    
    Inherits from obj:`IMAQdxCameraWorker`. Defines :obj:`interface_class` and overloads
    :obj:`get_attributes_as_dict` to use DCAMCameraWorker.get_attributes() method."""
    interface_class = DCAM_Camera

    def save_images(self):
        with h5py.File(self.h5_filepath, 'r+') as f:
            # Use orientation for image path, device_name if orientation unspecified
            if self.orientation is not None:
                image_path = 'images/' + self.orientation
            else:
                image_path = 'images/' + self.device_name
            image_group = f.require_group(image_path)
            image_group.attrs['camera'] = self.device_name

            # Save camera attributes to the HDF5 file:
            if self.attributes_to_save is not None:
                set_attributes(image_group, self.attributes_to_save)

            # Whether we failed to get all the expected exposures:
            image_group.attrs['failed_shot'] = len(self.images) != len(self.exposures)

            # key the images by name and frametype. Allow for the case of there being
            # multiple images with the same name and frametype. In this case we will
            # save an array of images in a single dataset.
            images = {
                (exposure['name'], exposure['frametype'], exposure['saving']): []
                for exposure in self.exposures
            }

            # Iterate over expected exposures, sorted by acquisition time, to match them
            # up with the acquired images:
            self.exposures.sort(order='t')
            ii=0
            for image, exposure in zip(self.images, self.exposures):
                if exposure['saving']:
                    ii+=1
                    images[(exposure['name'], exposure['frametype'], exposure['saving'])].append(image)
                    print(f"Saving {ii}/{sum(self.exposures['saving'])} images.")

            # Save images to the HDF5 file:
            
            for (name, frametype, saving), imagelist in images.items():
                if saving:
                    data = imagelist[0] if len(imagelist) == 1 else np.array(imagelist)
                    print(f"Saving frame(s) {name}/{frametype}.")
                    group = image_group.require_group(name)
                    dset = group.create_dataset(
                        frametype, data=data, dtype='uint16', compression='gzip'
                    )
                    # Specify this dataset should be viewed as an image
                    dset.attrs['CLASS'] = np.string_('IMAGE')
                    dset.attrs['IMAGE_VERSION'] = np.string_('1.2')
                    dset.attrs['IMAGE_SUBCLASS'] = np.string_('IMAGE_GRAYSCALE')
                    dset.attrs['IMAGE_WHITE_IS_ZERO'] = np.uint8(0)

    def save_image_now(self, new_image, index=0):
        with h5py.File(self.h5_filepath, 'r+') as f:
            # Use orientation for image path, device_name if orientation unspecified
            if self.orientation is not None:
                image_path = 'images/' + self.orientation
            else:
                image_path = 'images/' + self.device_name
            image_group = f.require_group(image_path)
            image_group.attrs['camera'] = self.device_name

            # Save camera attributes to the HDF5 file:
            if self.attributes_to_save is not None:
                set_attributes(image_group, self.attributes_to_save)

            # Whether we failed to get all the expected exposures:
            image_group.attrs['failed_shot'] = len(self.images) != len(self.exposures)

            # key the images by name and frametype. Allow for the case of there being
            # multiple images with the same name and frametype. In this case we will
            # save an array of images in a single dataset.
            images = {
                (exposure['name'], exposure['frametype'], exposure['saving']): []
                for exposure in self.exposures
            }

            # Iterate over expected exposures, sorted by acquisition time, to match them
            # up with the acquired images:
            self.exposures.sort(order='t')

            last_exposure=self.exposures[index]
            name=last_exposure['name']
            frametype=last_exposure['frametype']
            to_be_saved=last_exposure['saving']

            if to_be_saved:
                images[(name, frametype, to_be_saved)]=new_image
                print(f"Saving {index+1}/{sum(self.exposures['saving'])} images.")
                # Save images to the HDF5 file:
                data = new_image
                print(f"Saving frame(s) {name}/{frametype}.")
                group = image_group.require_group(name)
                dset = group.create_dataset(
                    frametype, data=data, dtype='uint16', compression='gzip'
                )
                # Specify this dataset should be viewed as an image
                dset.attrs['CLASS'] = np.string_('IMAGE')
                dset.attrs['IMAGE_VERSION'] = np.string_('1.2')
                dset.attrs['IMAGE_SUBCLASS'] = np.string_('IMAGE_GRAYSCALE')
                dset.attrs['IMAGE_WHITE_IS_ZERO'] = np.uint8(0)

    def acquire_and_save(self, n_images, images):
        """Acquire and save n_images to the images list."""

        print(f"Attempting to grab {n_images} images.")
        for i in range(n_images):
            if self.camera._abort_acquisition:
                print("Abort during acquisition.")
                self.camera._abort_acquisition = False
                return
            new_images=self.camera.grab(bufferNo=i)
            images.append(new_images)
            self.save_image_now(new_images, index=i)

            print(f"Got image {i+1} of {n_images}.")                    

        print(f"Got {len(images)} of {n_images} images.")
        # return images       

    def get_attributes_as_dict(self, visibility_level):
        """Return a dict of the attributes of the camera for the given visibility
        level
        
        Args:
            visibility_level (str): Normally configures level of attribute detail
                to return. Is not used by FlyCapture2_Camera.
        """
        if self.mock:
            return IMAQdxCameraWorker.get_attributes_as_dict(self,visibility_level)
        else:
            return self.camera.get_attributes(visibility_level)

    def transition_to_buffered(self, device_name, h5_filepath, initial_values, fresh):
        print(datetime.datetime.now())
        if getattr(self, 'is_remote', False):
            h5_filepath = path_to_local(h5_filepath)
        if self.continuous_thread is not None:
            # Pause continuous acquistion during transition_to_buffered:
            self.stop_continuous(pause=True)
        with h5py.File(h5_filepath, 'r') as f:
            group = f['devices'][self.device_name]
            if not 'EXPOSURES' in group:
                return {}
            self.h5_filepath = h5_filepath
            self.exposures = group['EXPOSURES'][:]
            self.n_images = len(self.exposures)

            # Get the camera_attributes from the device_properties
            properties = labscript_utils.properties.get(
                f, self.device_name, 'device_properties'
            )
            camera_attributes = properties['camera_attributes']
            self.stop_acquisition_timeout = properties['stop_acquisition_timeout']
            self.exception_on_failed_shot = properties['exception_on_failed_shot']
            saved_attr_level = properties['saved_attribute_visibility_level']
            self.camera.exception_on_failed_shot = self.exception_on_failed_shot
        # Only reprogram attributes that differ from those last programmed in, or all of
        # them if a fresh reprogramming was requested:
        if fresh:
            self.smart_cache = {}
        self.set_attributes_smart(camera_attributes)
        # Get the camera attributes, so that we can save them to the H5 file:
        if saved_attr_level is not None:
            self.attributes_to_save = self.get_attributes_as_dict(saved_attr_level)
        else:
            self.attributes_to_save = None
        print(f"Configuring Orca camera for {self.n_images} images.")
        self.camera.configure_acquisition(continuous=False, bufferCount=self.n_images)

        self.images = []

        # Start the acquisition thread to grab the images:
        
        if take_and_save:
            print("Starting Orca acquisition and saving thread.")
            self.acquisition_thread = threading.Thread(
                target=self.acquire_and_save,
                args=(self.n_images, self.images),
                daemon=True,
            )
        else:
            print("Starting Orca acquisition thread.")
            self.acquisition_thread = threading.Thread(
                target=self.camera.grab_multiple,
                args=(self.n_images, self.images),
                daemon=True,
            )
        self.acquisition_thread.start()
        print(datetime.datetime.now())
        return {}

    def transition_to_manual(self):

        if self.h5_filepath is None:
            print('No camera exposures in this shot.\n')
            return True
        assert self.acquisition_thread is not None
        self.acquisition_thread.join(timeout=self.stop_acquisition_timeout)
        if self.acquisition_thread.is_alive():
            msg = """Acquisition thread did not finish. Likely did not acquire expected
                number of images. Check triggering is connected/configured correctly"""
            if self.exception_on_failed_shot:
                self.abort()
                raise RuntimeError(dedent(msg))
            else:
                self.camera.abort_acquisition()
                self.acquisition_thread.join()
                print(dedent(msg), file=sys.stderr)
        self.acquisition_thread = None

        print("Stopping acquisition.")
        self.camera.stop_acquisition()

        if not take_and_save:
            self.save_images()

        # If the images are all the same shape, send them to the GUI for display:
        try:
            image_block = np.stack(self.images)
        except ValueError:
            print("Cannot display images in the GUI, they are not all the same shape")
        else:
            self._send_image_to_parent(image_block)

        self.images = None
        self.n_images = None
        self.attributes_to_save = None
        self.exposures = None
        self.h5_filepath = None
        self.stop_acquisition_timeout = None
        self.exception_on_failed_shot = None
        print("Setting manual mode camera attributes.\n")
        self.set_attributes_smart(self.manual_mode_camera_attributes)
        if self.continuous_dt is not None:
            # If continuous manual mode acquisition was in progress before the bufferd
            # run, resume it:
            self.start_continuous(self.continuous_dt)
        return True




