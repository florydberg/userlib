#___________________________________________________________________________________#
from labscript import start, stop #                                                 |
from labscript_utils import import_or_reload #                                      |
import_or_reload('labscriptlib.Sr.SUB_ROUTINES') #                                  |
from labscriptlib.Sr.SUB_ROUTINES import * #                                        |
#\______________________________ GENERAL LIBRARIES ________________________________/#

if True: ## Selects ##
    shieldSingle = GLOBALS['ShieldSingle']
    shieldMulti = GLOBALS['ShieldMulti']

    sel_mot_blue = GLOBALS['mot_blue']
    sel_mot_red = GLOBALS['mot_red']
    sel_mot_red_sf = GLOBALS['mot_red_sf']
    sel_tweezer = GLOBALS['tweezers']

    sel_fluo_image = GLOBALS['imaging_fluo']
    sel_abs_image = GLOBALS['imaging_abs']

    sel_imaging_beam = GLOBALS['beam_imaging'] #'abs', 'tweez', '3Dmot'

    sel_camera_fluo = GLOBALS['camera_fluo'] #'andor', 'orca', 'basler_abs', 'basler_fluo'
    sel_camera_abs = GLOBALS['camera_abs'] #'basler_abs', 'andor', 'basler_fluo'

    orca_trigger_delay=7.2*usec*(4+1) + 4*usec # (4+1)*7us is in the manual as the longest delay + jitter pg. 49/82; we add 4us as an additonal buffer (total 40us)
    Orca_Camera_fluo_readout=(2304/2)*7.2*usec + (1/17.6)*sec # For USB, rolling shutter timing + inverse max frame rate (fps) at 4096x2304 pixels the readout time is 1/17.6 (for the whole image to be readout) pg. 60/82 of manual
    Orca_Labscript_delay= 8.3*msec
    if co:
        Orca_Camera.camera_attributes['EXPOSURE TIME']=GLOBALS['FluoImaging_duration']*1e-6
        if GLOBALS['Orca_ROI']=='full':
            Orca_Camera.camera_attributes['SUBARRAY MODE']=2
            Orca_Camera.camera_attributes['SUBARRAY HSIZE']=4096.0
            Orca_Camera.camera_attributes['SUBARRAY VSIZE']=2304.0
            Orca_Camera.camera_attributes['SUBARRAY HPOS']=0
            Orca_Camera.camera_attributes['SUBARRAY VPOS']=0
        elif GLOBALS['Orca_ROI']=='mot':
            Orca_Camera.camera_attributes['SUBARRAY MODE']=2
            Orca_Camera.camera_attributes['SUBARRAY HSIZE']=1000 #x
            Orca_Camera.camera_attributes['SUBARRAY VSIZE']=1000 #y
            Orca_Camera.camera_attributes['SUBARRAY HPOS']=425*4
            Orca_Camera.camera_attributes['SUBARRAY VPOS']=100*4
        elif GLOBALS['Orca_ROI']=='tweez':
            Orca_Camera.camera_attributes['SUBARRAY MODE']=2
            Orca_Camera.camera_attributes['SUBARRAY HSIZE']=100 #x
            Orca_Camera.camera_attributes['SUBARRAY VSIZE']=100 #y
            Orca_Camera.camera_attributes['SUBARRAY HPOS']=530*4
            Orca_Camera.camera_attributes['SUBARRAY VPOS']=206*4
            

grid_size = GLOBALS['grid_size']

start()

t+=standingTweezer(t, 'all', amplitude=100, duration = 10)*150000
awg_trigger.go_high(t) # Trigger the AWG to start the sequence

# Basler_Camera_extra_trigger.go_high(t)


# for ii in range(0,grid_size**2-1):
#     t+=movingstandingTweezer(t,  range(0,grid_size**2),  ii,  ii+1, 100, 10)*150000
#     t+=500*usec


stop(t+1*sec)