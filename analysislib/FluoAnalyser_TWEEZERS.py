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
        V_MAX=0.15 #.15 for blue .40 for red

        Imag_beam_Power=440e-6 #W   #TODO: update this value with the measure we have to take
        waist_0=6.667e-3 #m
        I=2*Imag_beam_Power/(np.pi*waist_0**2)
        lambda_laser = 461*1e-9
        delta=0
        Gam=32e6

        h=6.626e-34 #JHz^-1
        c=2.99e8 # m/s

        I_sat = (np.pi* h*c*Gam)/(3*lambda_laser**3) # previous calculation was 67.6
        print('saturation = '+ str(round((I/I_sat)*100)/100))   
        # absorption_coefficient = 0.02 
        # atom_mass = 1.67*88e-27  # mass of a single atom (in kilograms)

        pixel_size = 1.85e-6  # meters per pixel (Basler)
        pix=pixel_size*500/150 # effective pixel size
        pixArea=pix*pix #pixArea = Sat
        print(pixArea)
        delta=0
        Gam=32e6
        sigma_0=3*lambda_laser**2/(2*np.pi)  #  previous calculation was 9.7e-14 
        sigma=sigma_0/(1+(2*delta/Gam)**2 + I/I_sat)
        print('sigma = '+ str(I_sat))
        print('sigma = '+ str(sigma))

    def gaussian_2d(xy, amplitude, xo, yo, sigma_x, sigma_y, theta, offset):
        theta = theta * np.pi*0
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

    def MotPlot(MotSpot, rmin = None, rmax = None):
        if rmin == None:
            rmin=np.amin(MotSpot)
        if rmax == None:
            rmax=np.amax(MotSpot)
        plt.figure(figsize=(10, 10))
        h, w = MotSpot.shape 
        h = h * 2
        w = w * 2
        intx = np.sum(MotSpot, axis=0)
        inty = np.sum(MotSpot, axis=1)
        gs = gridspec.GridSpec(2, 2, width_ratios=[w * .2, w], height_ratios=[ h, h * .2])
        ax = [plt.subplot(gs[3]), plt.subplot(gs[0]), plt.subplot(gs[1])]
        ax[0].plot(intx, 'b')       
        ax[1].plot(inty[::-1], np.linspace(1, inty.shape, MOTray*2), 'b') 
        ax[2].imshow(MotSpot, cmap='viridis',vmin=rmin, vmax=rmax) 
        plt.title('Mot Spot')
        plt.gca().add_patch(TweezArea3)
        plt.gca().add_patch(TweezArea2)
        plt.gca().add_patch(TweezArea1)
        save_imag(plt, 'mot_fluo')
        plt.show() 

    def TweezerAnalysis(TweezerSpot, ii, plotting=False, GaussFit=False):
        h, w = TweezerSpot.shape 
        h = h * 2
        w = w * 2
        totphotons=np.sum(TweezerSpot)
        TweezerPoint=TweezerSpot[Tray-2:Tray+3, Tray-2:Tray+3]
        mean_count=mean(TweezerPoint)
        var_count=var(TweezerPoint)
        shot.save_result('mean_tweezer_'+str(ii), mean_count)
        shot.save_result('variance_tweezer_'+str(ii), var_count)

        if GaussFit:
            x = np.linspace(1, Tray*2, Tray*2)
            y = np.linspace(1, Tray*2, Tray*2)
            xx, yy = np.meshgrid(x, y)
            X = xx.ravel(order='F')
            Y = yy.ravel(order='F')
            initial_guess = (260, Tray, Tray, Tray/2, Tray/2, 0.01, 0.01)
            try:
                popt, cov = curve_fit(gaussian_2d, (X, Y), TweezerSpot.ravel(order='F'), p0=initial_guess)
            except:
                popt = [26, 1, 1, 1, 1, 0, 0]
    
            amplitude, xo, yo, sigma_x, sigma_y, theta, offset = popt
            popt=amplitude, xo, yo, sigma_x, sigma_y, theta, offset  
            std_dev=(sigma_x+sigma_y)/2
            fit_data = gaussian_2d((X, Y), *popt)
            fitdata = fit_data.reshape((Tray*2, Tray*2), order='F')
            gauy = np.sum(fitdata, axis=1)
            gaux = np.sum(fitdata, axis=0)
            shot.save_result('peak_tweezer_'+str(ii), amplitude)
            shot.save_result('deviation_tweezer_'+str(ii), std_dev)

        if plotting:
            plt.figure(figsize=(10, 10))
            gs = gridspec.GridSpec(2, 2, width_ratios=[w * .2, w], height_ratios=[ h, h * .2])
            ax = [plt.subplot(gs[3]), plt.subplot(gs[0]), plt.subplot(gs[1])]
            ax[2].imshow(TweezerSpot, cmap='viridis',vmin=np.amin(MotSpot) , vmax=np.amax(MotSpot) )
            plt.title('Tweezer '+ str(ii) + ' Spot')
            intx = np.sum(TweezerSpot, axis=0)
            inty = np.sum(TweezerSpot, axis=1)
            ax[0].plot(intx, 'b')
            ax[1].plot(inty[::-1], np.linspace(1, inty.shape, Tray*2), 'b') 
            x_label1="mean = %d , variance = %d" %(round(mean_count), var_count)
            TweezArea=patches.Rectangle([Tray-2,Tray-2], 4, 4, linewidth=1, edgecolor='r', facecolor='none')
            plt.gca().add_patch(TweezArea)
            plt.legend(['Tweezer Integration Area'], loc ="lower right")
            x_label2=''
            if GaussFit:
                x_label2=", peak = %d , std_dev = %d " %(round(amplitude), std_dev)
                ax[0].plot(gaux, 'r')
                ax[1].plot(gauy[::-1], np.linspace(1, inty.shape, Tray*2), 'r')
            plt.xlabel(x_label1+x_label2)
            plt.show() 
            save_imag(plt, 'tweez_fluo_'+ str(ii))

        

######################
scan_parameter='ImagingTweez_Frq'
scan_unit='MHz'
######################
plt.style.use("default")

with Run(path).open('r+') as shot:
    start_time = time.time()
    data_frame=data(path)

    img={}
    for i in ['TweezFluo']:    
        shot_image=shot.get_image('Orca_Camera',str(i),'frame')  # Obtaining multiple images and averaging them:
        if int(data_frame['n_loop'])>1: img[str(i)] = np.average(shot_image.astype(np.float32),axis=0)
        else: img[str(i)]=shot_image.astype(np.float32)

    if True: #ROIS
        # MOT0=[2600,900]
        MOT0=[2357,843]
        MOTray=50

        T1=[50,30]
        T2=[50,50]
        T3=[50,70]
        Tray=6
        
        FluoImag=img['TweezFluo']
        FluoImag-=200 #offset removal
        MOTArea=patches.Circle(MOT0, MOTray, linewidth=1, edgecolor='r', facecolor='none')
        TweezArea1=patches.Circle(T1, Tray, linewidth=1, edgecolor='r', facecolor='none')
        TweezArea2=patches.Circle(T2, Tray, linewidth=1, edgecolor='r', facecolor='none')
        TweezArea3=patches.Circle(T3, Tray, linewidth=1, edgecolor='r', facecolor='none')

        MotSpot=FluoImag[MOT0[1]-MOTray:MOT0[1]+MOTray, MOT0[0]-MOTray:MOT0[0]+MOTray]
        TweezerSpot1=MotSpot[T1[1]-Tray:T1[1]+Tray, T1[0]-Tray:T1[0]+Tray]
        TweezerSpot2=MotSpot[T2[1]-Tray:T2[1]+Tray, T2[0]-Tray:T2[0]+Tray]
        TweezerSpot3=MotSpot[T3[1]-Tray:T3[1]+Tray, T3[0]-Tray:T3[0]+Tray]
    
    if False: #FUllFrame 
        plt.figure()
        plt.title('Orca Fluo')
        plt.gca().add_patch(MOTArea)
        plt.imshow(FluoImag, cmap='viridis' )
        plt.colorbar()
        plt.legend(['Red Mot Area'], loc ="lower right")
        save_imag(plt, 'orca_fluo' )
        plt.show() 

    # ## MOT spot
    MotPlot(MotSpot,0,50)

    # Tweezer Spot n 1
    TweezerAnalysis(TweezerSpot1, 1, plotting=True, GaussFit=False)

    # Tweezer Spot n 2
    TweezerAnalysis(TweezerSpot2, 2)

    # Tweezer Spot n 3
    TweezerAnalysis(TweezerSpot3, 3)

shot.save_result('background', mean(MotSpot[0:5,0:5]))
shot.save_result('scan_parameter', scan_parameter)
shot.save_result('scan_unit', scan_unit)
saving_script(path)
