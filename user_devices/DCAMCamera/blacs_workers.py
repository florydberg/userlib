#####################################################################
#                                                                   #
# /user_devices/DCAMCamera/blacs_workers.py                         #
#                                                                   #
# Jan 2023, Marvin Holten                                           #
#                                                                   #
# Sep 2024, Andrea Fantini                                          #
#####################################################################

from labscript_devices.IMAQdxCamera.blacs_workers import IMAQdxCameraWorker

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
        self.timeout = 5000

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


