from lyse import *
from lyse import Run
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
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy import ndimage
ts=time.time()
datetime.datetime.now()
dt=datetime.datetime.now().date()

if True: #functions definition
    if True:  # Constants and Image Analysis  
        pixel_size = 4.6e-6  # meters per pixel (Orca magnified)
        effective_pixel_size = 1.104 # M = f_tubelens/f_eff; pixel_eff = pixel_size/M, ftubelens = 100, f_eff = 24mm
 
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
        tm = datetime.datetime.now()
        img_name=str(dt) + '_' + tm.strftime("%H") + tm.strftime("%M") + tm.strftime("%S") + '_' +tm.strftime("%f")
        print(path)
        one_level_up = os.path.dirname(path)
        plt.savefig(one_level_up + '/' + img_name +  '_' + picname + ".png")
        print(picname + ' saved')

    def MotPlot(MotSpot, rmin = None, rmax = None, GaussFit=False):
        MOTray=round(size(MotSpot,1)/2)
        # print(MOTray)
        if rmin == None:
            rmin=np.amin(MotSpot)
        if rmax == None:
            rmax=np.amax(MotSpot)
        plt.figure(figsize=(10, 10))
        h, w = MotSpot.shape 
        h = h * 2
        w = w * 2
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
        intx = np.sum(MotSpot, axis=0)
        inty = np.sum(MotSpot, axis=1)
        
        n_ticks=7
        x_values=np.round(linspace(0,(MotSpot.shape[0])*pixel_size*1000*(n_ticks-1)/n_ticks, n_ticks),2)
        x_ticks=np.arange(0, MotSpot.shape[0], MotSpot.shape[0]/n_ticks)
        y_values=np.round(linspace(0,(MotSpot.shape[0])*pixel_size*1000*(n_ticks-1)/n_ticks, n_ticks),2)
        y_ticks=np.arange(0, MotSpot.shape[1], MotSpot.shape[0]/n_ticks)

        gs = gridspec.GridSpec(2, 2, width_ratios=[w * .2, w], height_ratios=[ h, h * .2])
        ax = [plt.subplot(gs[3]), plt.subplot(gs[0]), plt.subplot(gs[1])]
        ax[0].plot(intx, 'b')  
        if GaussFit:     
            ax[0].plot(np.linspace(1, intx.shape, MOTray*2)*effective_pixel_size, gaux,  'r')       
        ax[1].plot(inty[::-1], np.linspace(1, inty.shape, MOTray*2), 'b') 
        if GaussFit:
            pixel_line=np.linspace(1, inty.shape, MOTray*2)*effective_pixel_size
            ax[1].plot(gauy[::-1], pixel_line, 'r') 
        ax[2].imshow(MotSpot, cmap='plasma',vmin=rmin, vmax=rmax) 
        plt.rcParams.update({'font.size': 20})
        plt.title('Mot Spot')
        # if not GaussFit:
        #     # plt.gca().add_patch(back)
        plt.gca().add_patch(TweezArea3)
        plt.gca().add_patch(TweezArea2)
        plt.gca().add_patch(TweezArea1)
        if saving_plots: save_imag(plt, 'mot_fluo')
        if True:
            plt.xticks(ticks=x_ticks, labels=x_values)
            plt.yticks(ticks=y_ticks, labels=y_values)
            plt.xlabel('mm')
            plt.ylabel('mm')
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
        plt.show() 

    def TweezerAnalysis(TweezerSpot, ii, plotting=False, GaussFit=False):
        h, w = TweezerSpot.shape 
        h = h * 2
        w = w * 2

        TweezerPoint=TweezerSpot[Tray-waist:Tray+waist, Tray-waist:Tray+waist]
        mean_count=mean(TweezerPoint)
        photon_count=sum(TweezerPoint)/10
        var_count=var(TweezerPoint)
        max_count=np.max(TweezerPoint)
        shot.save_result('mean_tweezer_'+str(ii), mean_count)
        shot.save_result('max_tweezer_'+str(ii), max_count)
        shot.save_result('variance_tweezer_'+str(ii), var_count)
        shot.save_result('photon_tweezer_'+str(ii), photon_count)
        shot.save_result('atom_in_tweezer_'+str(ii), int(photon_count>atom_presence_threshold))

        if GaussFit:
            x = np.linspace(1, Tray*2, Tray*2)
            y = np.linspace(1, Tray*2, Tray*2)
            xx, yy = np.meshgrid(x, y)
            X = xx.ravel(order='F')
            Y = yy.ravel(order='F')
            initial_guess = (260, Tray, Tray, Tray/2, Tray/2, 0.01, 0.01)
            try:
                popt, _ = curve_fit(gaussian_2d, (X, Y), TweezerSpot.ravel(order='F'), p0=initial_guess)
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
            ax[2].imshow(TweezerSpot, cmap='plasma',vmin=0 , vmax=FLUO_MAX )
            plt.title('Tweezer '+ str(ii) + ' Spot')
            intx = np.sum(TweezerSpot, axis=0)
            inty = np.sum(TweezerSpot, axis=1)
            ax[0].plot(intx, 'b')
            ax[1].plot(inty[::-1], np.linspace(1, inty.shape, Tray*2), 'b') 
            x_label1="mean = %d , variance = %d" %(round(mean_count), var_count)

            TweezArea=patches.Rectangle([Tray-waist,Tray-waist], tweezROI, tweezROI, linewidth=1, edgecolor='r', facecolor='none')

            plt.gca().add_patch(TweezArea)
            plt.legend(['Tweezer Integration Area'], loc ="lower right")
            x_label2=''
            if GaussFit:
                x_label2=", peak = %d , std_dev = %d " %(round(amplitude), std_dev)
                ax[0].plot(gaux, 'r')
                ax[1].plot(gauy[::-1], np.linspace(1, inty.shape, Tray*2), 'r')
            plt.xlabel(x_label1+x_label2)
            plt.show() 
            if saving_plots: save_imag(plt, 'tweez_fluo_'+ str(ii))

    def gaussian_2d(xy, amplitude, xo, yo, sigma_x, sigma_y, theta, offset):
        theta = theta * np.pi
        x, y = xy
        xo = float(xo)
        yo = float(yo)
        a = (np.cos(theta)**2) / (2 * sigma_x**2) + (np.sin(theta)**2) / (2 * sigma_y**2)
        b = -(np.sin(2 * theta)) / (4 * sigma_x**2) + (np.sin(2 * theta)) / (4 * sigma_y**2)
        c = (np.sin(theta)**2) / (2 * sigma_x**2) + (np.cos(theta)**2) / (2 * sigma_y**2)
        return amplitude * np.exp(-(a * (x - xo)**2 + 2 * b * (x - xo) * (y - yo) + c * (y - yo)**2)) + offset
    
    def gaussian_2d_symmetric(coords, A, x0, y0, sigma, B):
        x, y = coords
        return A * np.exp(-((x - x0)**2 + (y - y0)**2) / (2 * sigma**2)) + B

    def fit_gaussian_2d(image, simmetric=True):
        # Coordinate griglia
        y = np.arange(image.shape[0])
        x = np.arange(image.shape[1])
        x, y = np.meshgrid(x, y)

        # Stime iniziali
        A_init = image.max() - image.min()
        B_init = image.min()
        x0_init = np.sum(x * image) / np.sum(image)
        y0_init = np.sum(y * image) / np.sum(image)
        sigma_init = np.std(image)

        

        # Fit
        if simmetric:
            profile = gaussian_2d_symmetric
            initial_guess = (A_init, x0_init, y0_init, sigma_init, B_init)
        else:
            profile = gaussian_2d
            initial_guess = (A_init, x0_init, y0_init, sigma_init, sigma_init, 0, B_init)

        popt, pcov = curve_fit(
            profile,
            (x.ravel(), y.ravel()),
            image.ravel(),
            p0=initial_guess
        )

        return popt, pcov
    
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
    
def extract_beam_parameters(image, pixel_size=1.0):
    """
    Returns:
        [x_max, y_max], x_waist, y_waist

    where waist = full width at half maximum (measured directly, no fit)
    """

    # --- Find peak ---
    y_max, x_max = np.unravel_index(np.argmax(image), image.shape)
    peak_value = image[y_max, x_max]

    half_max = peak_value / 2.0

    # --- X profile (horizontal cut) ---
    profile_x = image[y_max, :]

    # Find indices where profile crosses half max
    indices_x = np.where(profile_x >= half_max)[0]

    if len(indices_x) > 1:
        x_left = indices_x[0]
        x_right = indices_x[-1]
        x_waist = (x_right - x_left) * pixel_size
    else:
        x_waist = np.nan

    # --- Y profile (vertical cut) ---
    profile_y = image[:, x_max]

    indices_y = np.where(profile_y >= half_max)[0]

    if len(indices_y) > 1:
        y_bottom = indices_y[0]
        y_top = indices_y[-1]
        y_waist = (y_top - y_bottom) * pixel_size
    else:
        y_waist = np.nan

    return [x_max, y_max], x_waist, y_waist

######################
saving_plots=True
tweezROI=8
waist=round(tweezROI/2)
atom_presence_threshold=30
pixel_dim=0.388 #um
FLUO_MAX = None

######################
plt.style.use("default")
path=path
try:
    with Run(path).open('r+') as shot:
        start_time = time.time()
        data_frame=data(path)
        ROI=data_frame['Orca_ROI']
        param1=data_frame['translator_stage_z']
        second_shot = data_frame['second_shot']
        
        img={}
        for i in ['TweezFluo']:    
            shot_image=shot.get_image('Orca_Camera',str(i),'frame')  # Obtaining multiple images and averaging them:
            if int(data_frame['n_loop'])>1: img[str(i)] = np.average(shot_image.astype(np.float32),axis=0)
            else: img[str(i)]=shot_image.astype(np.float32)

        FluoImag = img['TweezFluo']#[::-1, :]
        FluoImag-=200 #offset removal
        MOTray=50
        plt.figure(1)
        plt.title('Orca Fluo')
        plt.imshow(FluoImag, cmap='plasma', vmax=FLUO_MAX)
        plt.colorbar()

        if ROI=='full': #ROIS
            MOT0=[2360,2300-841] 
            MOTArea=patches.Circle(MOT0, MOTray, linewidth=1, edgecolor='r', facecolor='none')
            MotSpot=FluoImag[MOT0[1]-MOTray:MOT0[1]+MOTray, MOT0[0]-MOTray:MOT0[0]+MOTray]
            # plt.gca().add_patch(MOTArea)

            C_FOV=[2900, 1100]
            # C_FOV=[2444, 2300-860]
            C_Y=C_FOV[1]
            C_X=C_FOV[0]
            
            diff_lim_area=plt.Circle((C_X, C_Y), 200, linewidth=1, edgecolor='b', facecolor='none')
            
            plt.gca().add_patch(diff_lim_area)
            if True:
    
                mot_hsize, mot_vsize = 200, 200
                mot_hpos, mot_vpos = 650*4, 220*4

                MOT_roi = patches.Rectangle(
                    (mot_hpos, mot_vpos), mot_hsize, mot_vsize,
                    linewidth=2, edgecolor='orange', facecolor='none',
                    label='MOT ROI'
                )
                plt.gca().add_patch(MOT_roi)

                # -------- TWEEZER ROI (overlay) --------
                tweez_hsize, tweez_vsize = 50*2, 50*2
                tweez_hpos, tweez_vpos = 655 * 4, 240*4

                Tweezer_roi = patches.Rectangle(
                    (tweez_hpos, tweez_vpos), tweez_hsize, tweez_vsize,
                    linewidth=2, edgecolor='cyan', facecolor='none',
                    label='Tweezer ROI'
                )
                plt.gca().add_patch(Tweezer_roi)
            plt.legend([ 'Diffraction Limited Area', "mot region", "tweezer region"], loc ="lower right")

        elif ROI=='mot':
            MOT0=[round(np.shape(FluoImag)[0]/2),round(np.shape(FluoImag)[1]/2)] 
            MOTArea=patches.Circle(MOT0, MOTray, linewidth=1, edgecolor='r', facecolor='none')
            MotSpot=FluoImag[MOT0[1]-MOTray:MOT0[1]+MOTray, MOT0[0]-MOTray:MOT0[0]+MOTray]
            # plt.gca().add_patch(MOTArea)
        elif ROI=='tweez':
            MOTArea=patches.Circle(MOTray, MOTray, linewidth=1, edgecolor='r', facecolor='none')
            MotSpot=FluoImag

        # plt.legend(['Tweezer Area', 'FOV Area', 'Diffraction Limited Area'], loc ="lower right")


        [x_max, y_max], x_waist, y_waist = extract_beam_parameters(FluoImag, pixel_dim)

        plt.xlabel(
            f"Parameter value {param1} | "
            f"Max at [{x_max/pixel_dim:.2f}, {y_max/pixel_dim:.2f}] | "
            f"FWHM = ({x_waist:.2f}, {y_waist:.2f}) um"
        )

        # plt.imshow(FluoImag[y_max-200:y_max+200, x_max-200:x_max+200 ], cmap='plasma', vmax=FLUO_MAX)
        # plt.xlabel(f"Parameter value {param1} max at {np.max(FluoImag)} \\ Max value at [{x_max},{y_max}] with FWHM value {x_waist}, {y_waist}")
        plt.show()  

        Tray=4
        T1=[138,108]
        T2=[152,108]
        T3=[165,108]
        H3=[135,125]
        Hray=25
        back=patches.Rectangle([MOTray,round(MOTray/4)],waist*2, waist*2, linewidth=1, edgecolor='b', facecolor='none')
        
        TweezArea1=patches.Circle(T1, Tray, linewidth=1, edgecolor='b', facecolor='none')
        TweezArea2=patches.Circle(T2, Tray, linewidth=1, edgecolor='b', facecolor='none')
        TweezArea3=patches.Circle(T3, Tray, linewidth=1, edgecolor='b', facecolor='none')
        Halo3=patches.Circle(H3, Hray, linewidth=1, edgecolor='y', facecolor='none')

        TweezerSpot1=FluoImag[T1[1]-Tray:T1[1]+Tray, T1[0]-Tray:T1[0]+Tray]
        TweezerSpot2=FluoImag[T2[1]-Tray:T2[1]+Tray, T2[0]-Tray:T2[0]+Tray]
        TweezerSpot3=FluoImag[T3[1]-Tray:T3[1]+Tray, T3[0]-Tray:T3[0]+Tray]
        HaloSpot3=FluoImag[H3[1]-Hray:H3[1]+Hray, H3[0]-Hray:H3[0]+Hray]
        # MotPlot(MotSpot,0,50, GaussFit=False)
        plt.gca().add_patch(TweezArea3)
        plt.gca().add_patch(TweezArea2)
        plt.gca().add_patch(TweezArea1)
        plt.gca().add_patch(Halo3)

        shot.save_result('tw1_integral', (sum(TweezerSpot1)))
        shot.save_result('tw2_integral', (sum(TweezerSpot2)))
        shot.save_result('tw3_integral', (sum(TweezerSpot3)))
        shot.save_result('Halo_integral', (sum(HaloSpot3)))

        if saving_plots: save_imag(plt, 'orca_fluo' )

    if False: #find FOV
        plt.figure()
        # binfactor=4
        # RX=FluoImag.shape[1]
        # RY=FluoImag.shape[0]
        # datafit= bin_data(FluoImag, binfactor)
        # RXfit=int(RX/binfactor)
        # RYfit=int(RY/binfactor)
        # popt, pcov = fit_gaussian_2d(datafit)

        # A, x0, y0, sigma, B = popt
        [x0,y0]=C_FOV

        sigma=1755.503

        print("Center:")
        print(f"x0 = {x0:.3f}")
        print(f"y0 = {y0:.3f}")
        print(f"sigma = {sigma:.3f}")

        # Visualizzazione
        plt.imshow(FluoImag, origin='lower')
        plt.scatter(x0, y0, color='red', label='Centro stimato')
        FOV_area=plt.Circle((C_X, C_Y), 1000, linewidth=1, edgecolor='y', facecolor='none')
        plt.gca().add_patch(FOV_area)
        plt.legend(["center","FOV area"])
        plt.colorbar()
        plt.show()

    if False: #gaussian MOT fitting fro center detection
        binfactor=10
        RX=FluoImag.shape[1]
        RY=FluoImag.shape[0]
        datafit= bin_data(FluoImag, binfactor)
        RXfit=int(RX/binfactor)
        RYfit=int(RY/binfactor)
        popt, pcov = fit_gaussian_2d(datafit, simmetric=False)
        A, x0, y0, sigmax, sigmay, theta, B = popt

        sigmax=abs(sigmax)
        sigmay=abs(sigmay)
        
        print("Center:")
        print(f"x0 = {x0:.3f}")
        print(f"y0 = {y0:.3f}")
        print(f"sigmax = {sigmax:.3f}")
        print(f"sigmay = {sigmay:.3f}")
        print(f"theta = {theta:.3f}")
        print(f"B = {B:.3f}")
        # Visualizzazione
        plt.imshow(FluoImag, origin='lower', cmap="viridis")
        # plt.scatter(x0*binfactor, y0*binfactor, color='red', label='Centro stimato')
        # plt.legend()
        plt.xlabel(f'center = ({(x0*binfactor-C_FOV[0])*pixel_dim:.3f} um, {(y0*binfactor-C_FOV[1])*pixel_dim:.3f} um), sigmax = {sigmax*binfactor*pixel_dim:.3f} um, sigmay = {sigmay*binfactor*pixel_dim:.3f} um)')
        plt.colorbar()
        plt.title("Mot Fluporescence with gaussian fit")
        shot.save_result('centerx', (x0*binfactor-C_FOV[0])*pixel_dim)
        shot.save_result('centery', (y0*binfactor-C_FOV[1])*pixel_dim)

    sum_pixels=sum(FluoImag)
    shot.save_result('total_integral', (sum_pixels))
    saving_script(path)

except Exception as e:
    print("An error occurred during analysis:", e)