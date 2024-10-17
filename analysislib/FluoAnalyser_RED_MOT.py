from lyse import *
from runmanager.remote import *
from pylab import *
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
import matplotlib.patches as patches
import matplotlib.gridspec as gridspec
from labscript.labscript import *
import analysislib
from scipy.optimize import curve_fit, least_squares
import time # for testing speed of program
import datetime, time
ts=time.time()
datetime.datetime.now()
dt=datetime.datetime.now().date()

def bin_data(data, binfactor):
    # Get original shape
    original_shape = np.array(data.shape)

    # Check if the dimensions are divisible by binfactor
    if np.any(original_shape % binfactor != 0):
        # If not, crop the array to the nearest size that is divisible by binfactor
        new_shape = original_shape - (original_shape % binfactor)
        data = data[:new_shape[0], :new_shape[1]]
    
    # Calculate new shape
    new_shape = (data.shape[0] // binfactor, binfactor,
                 data.shape[1] // binfactor, binfactor)
    
    # Perform binning
    binned_data = data.reshape(new_shape).sum(axis=(1, 3)) / (binfactor**2)
    
    return binned_data


threshold_min=5
threshold_max=100
if True: #functions definition
    if True:  # Constants and Image Analysis  
        pixel_size = 4.6e-6  # meters per pixel (Orca magnified)
        effective_pixel_size = 1.104 # M = f_tubelens/f_eff; pixel_eff = pixel_size/M, ftubelens = 100, f_eff = 24mm
 

    def gaussian_2d(xy, amplitude, xo, yo, sigma_x, sigma_y, theta, offset):
        theta = theta * np.pi
        x, y = xy
        xo = float(xo)
        yo = float(yo)
        a = (np.cos(theta)**2) / (2 * sigma_x**2) + (np.sin(theta)**2) / (2 * sigma_y**2)
        b = -(np.sin(2 * theta)) / (4 * sigma_x**2) + (np.sin(2 * theta)) / (4 * sigma_y**2)
        c = (np.sin(theta)**2) / (2 * sigma_x**2) + (np.cos(theta)**2) / (2 * sigma_y**2)
        return amplitude * np.exp(-(a * (x - xo)**2 + 2 * b * (x - xo) * (y - yo) + c * (y - yo)**2)) + offset
                   
    def saving_script(path):
        with Run(path).open('r+') as shot:
            data_frame = data()
            # path=data_frame['filepath'].iloc[-1]
            file_path = os.path.realpath(__file__)
            prefix = os.path.dirname(analysislib.__file__)
            save_path = 'analysislib/' + file_path.replace(prefix, '').replace('\\', '/').replace('//', '/')
            with h5py.File(path, 'r') as hdf5_file:
                        if save_path not in hdf5_file:
                            # Don't try to save the same module script twice! (seems to at least
                            # double count __init__.py when you import an entire module as in
                            # from labscriptlib.stages import * where stages is a folder with an
                            # __init__.py file. Doesn't seem to want to double count files if
                            # you just import the contents of a file within a module
                            hdf5_file.create_dataset(save_path, data=open(file_path).read()) #TODO: fix the recreation of group in dataframe

            _vcs_cache_rlock = threading.RLock()
            def _file_watcher_callback(name, info, event):
                with _vcs_cache_rlock:
                    _vcs_cache[name] = _run_vcs_commands(name)
                _file_watcher = FileWatcher(_file_watcher_callback)
                with _vcs_cache_rlock:
                    if not path in _vcs_cache:
                        # Add file to watch list and create its entry in the cache.
                        _file_watcher.add_file(path)
                        _file_watcher_callback(path, None, None)

    def save_imag(plt, name):
        picname = name
        img_name=str(dt) + '_' + str(datetime.datetime.now().hour) + str(datetime.datetime.now().minute) + str(datetime.datetime.now().second)
        print(path)
        one_level_up = os.path.dirname(path)
        plt.savefig(one_level_up + '/' + img_name +  '_' + picname + ".png")
        print(picname + ' saved')

    def MotPlot(MotSpot):
        plt.figure(figsize=(20, 20))
        h, w = MotSpot.shape 
        h = h * 2
        w = w * 2
        GaussFit=1
        if GaussFit:
            x = np.linspace(1, MOTray*2, MOTray*2)
            y = np.linspace(1, MOTray*2, MOTray*2)
            xx, yy = np.meshgrid(x, y)
            X = xx.ravel(order='F')
            Y = yy.ravel(order='F')
            initial_guess = (260, MOTray, MOTray, MOTray/2, MOTray/2, 0.01, 0.01)
            try:
                popt, cov = curve_fit(gaussian_2d, (X, Y), MotSpot.ravel(order='F'), p0=initial_guess)
            except:
                popt = [26, 1, 1, 1, 1, 0, 0]
    
            amplitude, xo, yo, sigma_x, sigma_y, theta, offset = popt
            popt=amplitude, xo, yo, sigma_x, sigma_y, theta, offset  

            fit_data = gaussian_2d((X, Y), *popt)
            fitdata = fit_data.reshape((MOTray*2, MOTray*2), order='F')
            gauy = np.sum(fitdata, axis=1)
            gaux = np.sum(fitdata, axis=0)

        n_ticks=7

        x_values=np.round(linspace(0,(MotSpot.shape[0])*pixel_size*1000*(n_ticks-1)/n_ticks, n_ticks),2)

        x_ticks=np.arange(0, MotSpot.shape[0], MotSpot.shape[0]/n_ticks)

        y_values=np.round(linspace(0,(MotSpot.shape[0])*pixel_size*1000*(n_ticks-1)/n_ticks, n_ticks),2)

        y_ticks=np.arange(0, MotSpot.shape[1], MotSpot.shape[0]/n_ticks)


        gs = gridspec.GridSpec(2, 2, width_ratios=[w * .2, w], height_ratios=[ h, h * .2])
        ax = [plt.subplot(gs[3]), plt.subplot(gs[0]), plt.subplot(gs[1])]

        inty = np.sum(MotSpot, axis=1)
        pixel_line=np.linspace(1, inty.shape, MOTray*2)*effective_pixel_size
        ax[1].plot(inty[::-1], pixel_line, 'b') 
        if GaussFit:
            ax[1].plot(gauy[::-1], pixel_line, 'r') 

        intx = np.sum(MotSpot, axis=0)
        ax[0].plot(np.linspace(1, intx.shape, MOTray*2)*effective_pixel_size, intx,  'b')      
        if GaussFit:     
            ax[0].plot(np.linspace(1, intx.shape, MOTray*2)*effective_pixel_size, gaux,  'r')  

        plt.title('Red Mot Fluorescence')


        if True:
            # ax[2].colorbar()
            plt.xticks(ticks=x_ticks, labels=x_values)
            plt.yticks(ticks=y_ticks, labels=y_values)
            # plt.xlabel('um')
            plt.ylabel('um')
            # plt.show() 

        ax[2].imshow(MotSpot, cmap='plasma',vmin=np.amin(MotSpot) , vmax=np.amax(MotSpot) ) 

        if GaussFit:
            x_0=round(xo*effective_pixel_size)
            y_0=round(yo*effective_pixel_size)
            std_dev=(sigma_x+sigma_y)/2*effective_pixel_size
            # plt.colorbar(MotSpot)
            plt.xlabel("peak = %d , waist = %d, center = %a um" %(round(amplitude), std_dev, [x_0,y_0]))
            shot.save_result('peak_RedMot', amplitude)
            shot.save_result('waist_RedMot', std_dev)
            shot.save_result('center_RedMot', [x_0,y_0])
            shot.save_result('angle_RedMot', theta)
            shot.save_result('offset_RedMot', offset)

        save_imag(plt, 'mot_fluo')
        plt.show() 

        
######################
scan_parameter='TOF'
scan_unit='ms'
######################

with Run(path).open('r+') as shot:
    start_time = time.time()
    data_frame=data(path)

    img={}
    for i in ['TweezFluo']:    
        shot_image=shot.get_image('Orca_Camera',str(i),'frame')  # Obtaining multiple images and averaging them:
        if int(data_frame['n_loop'])>1: img[str(i)] = np.average(shot_image.astype(np.float32),axis=0)
        else: img[str(i)]=shot_image.astype(np.float32)

    if True: #ROIS
        MOT0=[2427,814]
        MOTray=200

        # T1=[81,57]
        # T2=[79,84]
        # T3=[80,112]

        Tray=10

        FluoImag=img['TweezFluo']
        FluoImag=FluoImag-201 #offset removal
        MOTArea=patches.Circle(MOT0, MOTray, linewidth=1, edgecolor='r', facecolor='none')

        MotSpot=FluoImag[MOT0[1]-MOTray:MOT0[1]+MOTray, MOT0[0]-MOTray:MOT0[0]+MOTray]

    
    if True: #FUllFrame 
        plt.figure()
        plt.title('Orca Fluo')
        plt.gca().add_patch(MOTArea)
        plt.imshow(FluoImag, cmap='plasma' )
        plt.colorbar()
        plt.legend(['Red Mot Area'], loc ="lower right")
        save_imag(plt, 'orca_fluo' )
        plt.show() 


    ## MOT spot
    MotPlot(MotSpot)

shot.save_result('scan_parameter', scan_parameter)
shot.save_result('scan_unit', scan_unit)
saving_script(path)
