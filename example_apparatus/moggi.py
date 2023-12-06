
    # DigitalChannels(name='DO_QRF2', parent_device=board0, connection='0x06', rack=0, max_channels=16)
    # # DigitalOut(name='QRF_trigger_0', parent_device=DO_QRF, connection=15, clockline=('QRF',True))
  
    #     # parent must be primary or secondary board. address and port is passed to MOGDevice.__init__
    # MOGLabs_QRF(name='QRF_2DMOT', parent_device=pb0_trg, addr='192.168.1.103', port=7802)
    # # MOGLabs_QRF(name='QRF_0', parent_device=DO_QRF, addr='192.168.1.190', port=7802)

    # QRF_DDS(name='test_DDS_0', parent_device=QRF_2DMOT, connection='channel 1', 
    #         table_mode=False,                         digital_gate={'device':DO_QRF2, 'connection': 0})
    # QRF_DDS(name='test_DDS_1', parent_device=QRF_2DMOT, connection='channel 2', 
    #         table_mode=True, trigger_each_step=False, digital_gate={'device':DO_QRF2, 'connection': 1})
    # QRF_DDS(name='test_DDS_2', parent_device=QRF_2DMOT, connection='channel 3', 
    #         table_mode=True, trigger_each_step=True, digital_gate={'device':DO_QRF2, 'connection': 2})
    # QRF_DDS(name='test_DDS_3', parent_device=QRF_2DMOT, connection='channel 4', 
    #         table_mode=True, trigger_each_step=True, digital_gate={'device':DO_QRF2, 'connection': 3})
    
    # DigitalChannels(name='DO_QRF3', parent_device=board0, connection='0x06', rack=0, max_channels=16)
    # # DigitalOut(name='QRF_trigger_0', parent_device=DO_QRF, connection=15, clockline=('QRF',True))

    #     # parent must be primary or secondary board. address and port is passed to MOGDevice.__init__
    # MOGLabs_QRF(name='QRF_3DMOT', parent_device=pb0_trg, addr='192.168.1.104', port=7802)
    # # MOGLabs_QRF(name='QRF_0', parent_device=DO_QRF, addr='192.168.1.190', port=7802)

    # QRF_DDS(name='test_DDS_0', parent_device=QRF_3DMOT, connection='channel 1', 
    #         table_mode=False,                         digital_gate={'device':DO_QRF3, 'connection': 0})
    # QRF_DDS(name='test_DDS_1', parent_device=QRF_3DMOT, connection='channel 2', 
    #         table_mode=True, trigger_each_step=False, digital_gate={'device':DO_QRF3, 'connection': 1})
    # QRF_DDS(name='test_DDS_2', parent_device=QRF_3DMOT, connection='channel 3', 
    #         table_mode=True, trigger_each_step=True, digital_gate={'device':DO_QRF3, 'connection': 2})
    # QRF_DDS(name='test_DDS_3', parent_device=QRF_3DMOT, connection='channel 4', 
    #         table_mode=True, trigger_each_step=True, digital_gate={'device':DO_QRF3, 'connection': 3})
    
    # DigitalChannels(name='DO_QRF4', parent_device=board0, connection='0x06', rack=0, max_channels=16)
    # # DigitalOut(name='QRF_trigger_0', parent_device=DO_QRF, connection=15, clockline=('QRF',True))   

    #     # parent must be primary or secondary board. address and port is passed to MOGDevice.__init__
    # MOGLabs_QRF(name='QRF_Imaging', parent_device=pb0_trg, addr='192.168.1.105', port=7802)
    # # MOGLabs_QRF(name='QRF_0', parent_device=DO_QRF, addr='192.168.1.190', port=7802)

    # QRF_DDS(name='test_DDS_0', parent_device=QRF_Imaging, connection='channel 1', 
    #         table_mode=False,                         digital_gate={'device':DO_QRF4, 'connection': 0})
    # QRF_DDS(name='test_DDS_1', parent_device=QRF_Imaging, connection='channel 2', 
    #         table_mode=True, trigger_each_step=False, digital_gate={'device':DO_QRF4, 'connection': 1})
    # QRF_DDS(name='test_DDS_2', parent_device=QRF_Imaging, connection='channel 3', 
    #         table_mode=True, trigger_each_step=True, digital_gate={'device':DO_QRF4, 'connection': 2})
    # QRF_DDS(name='test_DDS_3', parent_device=QRF_Imaging, connection='channel 4', 
    #         table_mode=True, trigger_each_step=True, digital_gate={'device':DO_QRF4, 'connection': 3})
    
    # DigitalChannels(name='DO_QRF5', parent_device=board0, connection='0x06', rack=0, max_channels=16)
    # # DigitalOut(name='QRF_trigger_0', parent_device=DO_QRF, connection=15, clockline=('QRF',True))   
    
    #         # parent must be primary or secondary board. address and port is passed to MOGDevice.__init__
    # MOGLabs_QRF(name='QRF_TweezImaging', parent_device=pb0_trg, addr='192.168.1.106', port=7802)
    # # MOGLabs_QRF(name='QRF_0', parent_device=DO_QRF, addr='192.168.1.190', port=7802)

    # QRF_DDS(name='test_DDS_0', parent_device=QRF_TweezImaging, connection='channel 1', 
    #         table_mode=False,                         digital_gate={'device':DO_QRF5, 'connection': 0})
    # QRF_DDS(name='test_DDS_1', parent_device=QRF_TweezImaging, connection='channel 2', 
    #         table_mode=True, trigger_each_step=False, digital_gate={'device':DO_QRF5, 'connection': 1})
    # QRF_DDS(name='test_DDS_2', parent_device=QRF_TweezImaging, connection='channel 3', 
    #         table_mode=True, trigger_each_step=True, digital_gate={'device':DO_QRF5, 'connection': 2})
    # QRF_DDS(name='test_DDS_3', parent_device=QRF_TweezImaging, connection='channel 4', 
    #         table_mode=True, trigger_each_step=True, digital_gate={'device':DO_QRF5, 'connection': 3})
    