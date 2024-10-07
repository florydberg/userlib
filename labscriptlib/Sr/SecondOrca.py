#___________________________________________________________________________________#
from labscript import start, stop #                                                 |
from labscript_utils import import_or_reload #                                      |
import_or_reload('labscriptlib.Sr.SUB_ROUTINES') #                                  |
from labscriptlib.Sr.SUB_ROUTINES import * #                                        |
#\______________________________ GENERAL LIBRARIES ________________________________/#

if True: ## Selects ##
    shieldSingle = GLOBALS['shieldSingle']
    shieldMulti = GLOBALS['shieldMulti']

    sel_mot_blue = GLOBALS['mot_blue']
    sel_mot_red = GLOBALS['mot_red']
    sel_mot_red_sf = GLOBALS['mot_red_sf']
    sel_tweezer = GLOBALS['tweezers']

    sel_fluo_image = GLOBALS['fluo_image']
    sel_abs_image = GLOBALS['abs_image']

    sel_imaging_beam = GLOBALS['imaging_beam'] #'abs', 'tweez', '3Dmot'

    sel_camera_fluo = GLOBALS['camera_fluo'] #'andor', 'orca', 'basler_abs', 'basler_fluo'
    sel_camera_abs = GLOBALS['camera_abs'] #'basler_abs', 'andor', 'basler_fluo'
    sel_table_red=GLOBALS['table_red']

start()
t+=250*msec

t=take_absorbImaging(t, GLOBALS['AbsImgPulse_duration'])
t+=5*msec
t+=Orca_Camera.expose(t,'fluo', trigger_duration=10, saving=True)


stop(t+2*msec)