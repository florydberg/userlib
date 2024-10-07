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

    def image_fft(image):

        # Compute the 2D Fourier Transform
        fft_result = np.fft.fft2(image)
        fft_result_shifted = np.fft.fftshift(fft_result)

        # Get the dimensions of the image
        rows, cols = image.shape
        crow, ccol = rows // 2, cols // 2  # Center of the image

        # Define a low-pass filter radius
        radius = 30

        # Create a circular mask for the low-pass filter
        y, x = np.ogrid[:rows, :cols]
        mask = np.sqrt((x - ccol)**2 + (y - crow)**2) <= radius

        # Apply the mask to the shifted FFT
        fft_result_lowpass = fft_result_shifted * mask

        # Display all images in log scale
        plt.figure(figsize=(15, 10))

        plt.subplot(221)
        im1 = plt.imshow(image, cmap='viridis', vmin=0, vmax=0.2)
        plt.title('Original Image')
        plt.colorbar(im1, ax=plt.gca())

        plt.subplot(222)
        plt.imshow(np.log(1 + np.abs(fft_result_shifted)), cmap='gray')
        plt.title('2D Fourier Transform')

        # Apply the inverse process
        image_fft = np.fft.ifft2(np.fft.ifftshift(fft_result_lowpass)).real

        plt.subplot(223)
        plt.imshow(np.log(1 + np.abs(fft_result_lowpass)), cmap='gray')
        plt.title('Low-pass Filtered Fourier Transform')

        plt.subplot(224)
        im2 = plt.imshow(image_fft, cmap='viridis', vmin=0, vmax=0.2)
        plt.title('Image after Inverse Fourier Transform')
        plt.colorbar(im2, ax=plt.gca())

        # plt.show()


        return image_fft
    
    def fit_gaussian(shot, value, RX, RY, data, scan_parameter, scan_unit, binfactor, N_2D, binning):
        

        # Define a 2D Gaussian function
        def gaussian_2d(xy, amplitude, xo, yo, sigma_x, sigma_y, theta, offset):
            theta = theta * np.pi
            x, y = xy
            xo = float(xo)
            yo = float(yo)
            a = (np.cos(theta)**2) / (2 * sigma_x**2) + (np.sin(theta)**2) / (2 * sigma_y**2)
            b = -(np.sin(2 * theta)) / (4 * sigma_x**2) + (np.sin(2 * theta)) / (4 * sigma_y**2)
            c = (np.sin(theta)**2) / (2 * sigma_x**2) + (np.cos(theta)**2) / (2 * sigma_y**2)
            return amplitude * np.exp(-(a * (x - xo)**2 + 2 * b * (x - xo) * (y - yo) + c * (y - yo)**2)) + offset
        
        x = np.linspace(1, RX, RX)
        y = np.linspace(1, RY, RY)
        xx, yy = np.meshgrid(x, y)
        X = xx.ravel(order='F')
        Y = yy.ravel(order='F')

        xxx = np.linspace(1, RX*binning, RX*binning)
        yyy = np.linspace(1, RY*binning, RY*binning)
        xxxx, yyyy = np.meshgrid(xxx, yyy)
        XXX = xxxx.ravel(order='F')
        YYY = yyyy.ravel(order='F')

        data[data<0]=0

        inty = np.sum(data, axis=1)
        intx = np.sum(data, axis=0)
        ampguess=min([np.max(data),np.max(intx)/(2*np.pi)**(1/2),np.max(inty)/(2*np.pi)**(1/2)]) #0.45
        
        # First Guess of Center
        edge=100
        x_0 = next(i for i in range(edge,len(intx)-edge) if intx[i] == max(intx[edge:len(intx)-edge]))
        y_0 = next(i for i in range(edge,len(inty)-edge) if inty[i] == max(inty[edge:len(inty)-edge]))

        print((x_0, len(inty)-y_0))


        initial_guess = (ampguess, x_0, y_0, 10, 10, 0.01, 0.01)  # Initial guess for amplitude, xo, yo, sigma_x, sigma_y, theta, offset
        low = [0, 0, 0, 0, 0, 0, -10]
        upper = [1e10, RX-RX/10, RY-RY/10, 2*RX, 2*RY, 0.25, 10]
        bounds = [low, upper]

        def residuals(params, xy, data):
            return gaussian_2d(xy, *params) - data

        if op_gauss_fit_internal:
            try:
                popt, _ = curve_fit(gaussian_2d, (X, Y), data.ravel(order='F'), p0=initial_guess, bounds=bounds)
            except:
                popt = [0, 1, 1, 1, 1, 0, 0]
            
            # Extract the parameters

            # data_ravel = data.ravel(order='F')
            # result = least_squares(residuals, initial_guess, bounds=bounds, args=((X, Y), data_ravel), method='trf')
            # popt = result.x
        else:
            popt = [0, 1, 1, 1, 1, 0, 0]
        
        # Extract parameter
        amplitude, xo, yo, sigma_x, sigma_y, theta, offset = popt
        popt_s=amplitude, xo, yo, sigma_x, sigma_y, theta, 0
        Npeak = (amplitude)* pixArea * binfactor**2 / sigma
        
        if not (threshold_min<sigma_x<threshold_max and threshold_min<sigma_y<threshold_max) :
            amplitude=0  
            Npeak=0  
            offset=0   
            xo=0
            yo=RY
        popt=amplitude, xo, yo, sigma_x, sigma_y, theta, offset  
        popt_s=amplitude, xo, yo, sigma_x, sigma_y, theta, 0
        
        # Print the fitted parameters
        print('amplitude', amplitude)
        print("Npeak:", Npeak)
        print("Center (x, y):", xo, RY - yo)
        print("Standard Deviations (sigma_x, sigma_y):", sigma_x, sigma_y)
        print("Theta: %s pi " % (round(theta * 100) / 100))
        print("offset: %s " % (round(offset* 100) / 100))


        # Generate the fitted Gaussian distribution
        fit_data = gaussian_2d((X, Y), *popt)
        fitdata = fit_data.reshape((RY, RX), order='F')
        print(-offset*RX*RY)
        fit_data_shifted = gaussian_2d((X, Y), *popt_s)
        fitdata_shifted = fit_data_shifted.reshape((RY, RX), order='F')

        fitN_of_atoms = np.sum(fitdata_shifted*pixArea*binfactor**2/sigma)
        print('\n----------------------------------------\n\n Gauss-Fit-Summed Number of atoms = %s 10^6' % (round(fitN_of_atoms / 10000) / 100))
        print('\n----------------------------------------\n')

        #########################  Plot the original data and the fitted Gaussian  #########################
        figure()
        plt.figure(figsize=(20, 10))
        # 2d image plot with profiles
        h, w = data.shape 
        h = h * 2
        w = w * 2

        gs = gridspec.GridSpec(3, 3, width_ratios=[w * .2, w, w], height_ratios=[h * .2, h, h * .2])

        ax = [plt.subplot(gs[3]), plt.subplot(gs[4]), plt.subplot(gs[7]), plt.subplot(gs[5])]
        bounds = [x.min(), x.max(), y.min(), y.max()]

        ax[1].imshow(data, cmap='viridis', vmin=0, vmax=V_MAX, extent=(x.min(), x.max(), y.min(), y.max()))

        ffit_data = gaussian_2d((XXX, YYY), *popt)
        print(len(xxx))
        ffitdata = ffit_data.reshape((RY*binning, RX*binning), order='F')

        inty = np.sum(data, axis=1)
        gauy = np.sum(fitdata, axis=1)
        ax[0].plot(inty[::-1], np.linspace(1, inty.shape, RX), 'b') 
        ax[0].plot(gauy[::-1], np.linspace(1, inty.shape, RX), 'r')


        intx = np.sum(data, axis=0)
        gaux = np.sum(fitdata, axis=0)
        ax[2].plot(intx, 'b')
        ax[2].plot(gaux, 'r')

        sigma_x=sigma_x*pix*binfactor
        sigma_y=sigma_y*pix*binfactor
        sigma_z=sigma_y

        #n_3D=fitN_of_atoms/(sigma_x*sigma_y*sigma_z*(2*np.pi)**(3/2))*1e-6 #in cm^3
        n_3D=Npeak/(sqrt(2*np.pi)*sigma_z*pixArea*binfactor**2)*1e-6 #in cm^3

        ax[3].imshow(fitdata_shifted, cmap='viridis', vmin=0, vmax=V_MAX, extent=(x.min(), x.max(), y.min(), y.max())) 
        plt.title('Fitted number of atoms = {}'.format("{:.2e}".format(fitN_of_atoms)))
        picname = " @ " + str(round(value,3)) +' '+ scan_unit +' of '+ scan_parameter
        plt.xlabel(str('3D peak density: %s in cm$^3$  \n sig_x,y:(%s um, %s um)\n Center=(%s, %s)\n %s' %
                    ("{:.2e}".format(n_3D), "{:.0e}".format(sigma_x*1e6), "{:.2e}".format(sigma_y*1e6),
                        round(xo * 100) / 100, round((RY - yo) * 100) / 100, str(picname))))

        # plt.colorbar()
        plt.savefig(picname + ".png")
        sigma_awg = (sigma_x+sigma_y)/2

        plt.show()

        shot.save_result('number_of_atoms', fitN_of_atoms)
        shot.save_result('peak_density', n_3D)
        shot.save_result('waistavg', sigma_awg)
        shot.save_result('waistx', sigma_x)
        shot.save_result('waisty', sigma_y)
        shot.save_result('centerx', xo*pix*binfactor*1e6)
        shot.save_result('centery', (RY - yo)*pix*binfactor*1e6)

        print('fitted results saved')

        print()

        # x_values=np.round(linspace(0,(700-5)*pixel_size*1000, 6),2)
        x_values=np.array([0,0.21,0.42,0.63,0.84,1.05])
        x_ticks=np.arange(0, data.shape[1],60)

        # y_values=np.round(linspace(0,(700-5)*pixel_size*1000, 6),2)
        # y_values=np.array([0,0.26,0.52,0.77,1.03,1.28])
        y_values=np.array([0,0.21,0.42,0.63,0.84,1.05])
        y_ticks=np.arange(0, data.shape[1],60)


        if True:
            plt.figure()
            plt.imshow(data, cmap='viridis', vmin=0, vmax=0.2)
            plt.colorbar()
            plt.xticks(ticks=x_ticks, labels=x_values)
            plt.yticks(ticks=y_ticks, labels=y_values)
            plt.xlabel('mm')
            plt.ylabel('mm')
            plt.show() 




        #plt.figure()
        #plt.imshow(data, cmap='viridis' )
        #plt.colorbar()
        #plt.yticks(ticks=y_ticks, labels=y_values)
        #plt.show() 
        
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

    def display_absorb_trio(img):
        gs = gridspec.GridSpec(1, 3)
        fig=plt.figure(figsize=(20, 10))

        ax1=plt.subplot(gs[0])
        name=('Atoms')
        plt.title(name)
        ax1.imshow(img['Atoms'], cmap='viridis',  vmin=0, vmax=np.amax(img['Atoms']))
        plt.show()

        ax2=plt.subplot(gs[1])
        name=('Probe')
        plt.title(name)
        ax2.imshow(img['Probe'], cmap='viridis',  vmin=0, vmax=np.amax(img['Atoms']))

        ax3=plt.subplot(gs[2])
        name=('Background')
        plt.title(name)
        
        ax3.imshow(img['Background'], cmap='viridis', vmin=0, vmax=np.amax(img['Atoms']))

        plt.show()

    def save_image(img,  path):
        print(path)
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

    def plot_single_image(MOT, corr, BEAM, img, i):
        plt.figure()
        plt.gca().add_patch(MOT)
        plt.gca().add_patch(corr)
        plt.gca().add_patch(BEAM)
        plt.title(str(i))
        plt.imshow(img[str(i)], cmap='viridis', vmin=0, vmax=np.amax(img['Atoms']) )
        plt.colorbar()
        plt.legend(['Atoms', 'Intensity correction'], loc ="lower right")
        plt.show() 

    def intensity_correction(up, down, dX, dY):
        Ia=np.sum(up[np.ix_(range(dY[0],dY[1]),range(dX[0],dX[1]))])
        Ib=np.sum(down[np.ix_(range(dY[0],dY[1]),range(dX[0],dX[1]))])
        return Ia/Ib

    def plot_up_down(up, down, value, scan_parameter, scan_unit, P0, RX, RY):  
        plt.figure()
        MOT1=patches.Rectangle(P0, RX, RY, linewidth=1, edgecolor='r', facecolor='none')    
        plt.imshow(up-down, cmap='viridis')
        plt.gca().add_patch(MOT1)
        plt.colorbar()
        plt.legend(['Atoms'], loc ="lower right")
        plt.title('Up-Down @'+str(value)+scan_unit+scan_parameter)
        plt.show()  

    def save_imag(plt, name):
        picname = name
        img_name=str(dt) + '_' + str(datetime.datetime.now().hour) + str(datetime.datetime.now().minute) + str(datetime.datetime.now().second)
        print(path)
        one_level_up = os.path.dirname(path)
        plt.savefig(one_level_up + '/' + img_name +  '_' + picname + ".png")
        print(picname + ' saved')

if True:# ROI Selection   
    P0=(50,0)   # Starting point for the atoms ROI
    RX=700
    RY=700
    # P0=(190,150)   # Starting point for the atoms ROI
    # RX=500
    # RY=500  

    DX=(P0[0], P0[0]+RX)
    DY=(P0[1], P0[1]+RY)

    p0=(300,600)   # Starting point for the correction area 
    rX=200
    rY=80

    dX=(p0[0], p0[0]+rX)
    dY=(p0[1], p0[1]+rY)

    b0=(500,400)    # Starting point for the Probe area
    ray=400       

    #FluoArea
    F0=[1500,500]
    FX=1000
    FY=500

######################
scan_parameter='Imaging_Frq'
scan_unit='MHz'

op_plotting = False #extra images
op_FFTfilter = False
op_binning = True
binfactor=2
op_gauss_fit = True
op_gauss_fit_internal = 1
BlaserAbs_for_Fluo=False

######################

with Run(path).open('r+') as shot:
    start_time = time.time()
    data_frame=data(path)

    img={}
    for i in ['TweezFluo']:    
        shot_image=shot.get_image('Orca_Camera',str(i),'frame')  # Obtaining multiple images and averaging them:
        if int(data_frame['n_loop'])>1: img[str(i)] = np.average(shot_image.astype(np.float32),axis=0)
        else: img[str(i)]=shot_image.astype(np.float32)

    T0=[2600,900]
    Tray=100

    cntrL_ROI=0
    if not cntrL_ROI:
        FluoImag=img['TweezFluo']
        TweezArea=patches.Circle(T0, Tray, linewidth=1, edgecolor='r', facecolor='none')
    else:
        FluoImag=img['TweezFluo'][F0[1]:F0[1]+FY, F0[0]:F0[0]+FX]
        TweezArea=patches.Circle([T0[0]-F0[0],T0[1]-F0[1]], Tray, linewidth=1, edgecolor='r', facecolor='none')
    # TweezerSpot=img['TweezFluo'][round(T0[1]-Tray/2):round(T0[1]+Tray/2), round(T0[0]+Tray/2):round(T0[0]+Tray/2)]

    TweezerSpot=img['TweezFluo'][T0[1]-Tray:T0[1]+Tray, T0[0]-Tray:T0[0]+Tray]
    totphotons=np.sum(TweezerSpot)
    
    plt.figure()
    plt.title('TweezFluo')
    plt.gca().add_patch(TweezArea)
    plt.imshow(FluoImag, cmap='viridis' )
    plt.colorbar()
    plt.legend(['Tweezer Integration Area'], loc ="lower right")
    plt.xlabel('Integrated Signal='+str(totphotons))
    save_imag(plt, 'fluo' )
    plt.show() 

    save_image(img,  path)


    plt.figure(figsize=(10, 10))
    # 2d image plot with profiles
    h, w = TweezerSpot.shape 
    h = h * 2
    w = w * 2

    gs = gridspec.GridSpec(2, 2, width_ratios=[w * .2, w], height_ratios=[ h, h * .2])
    ax = [plt.subplot(gs[3]), plt.subplot(gs[0]), plt.subplot(gs[1])]
    inty = np.sum(TweezerSpot, axis=1)
    ax[1].plot(inty[::-1], np.linspace(1, inty.shape, Tray*2), 'b') 
    intx = np.sum(TweezerSpot, axis=0)
    ax[0].plot(intx, 'b')       
    plt.title('TweezSpot')
    ax[2].imshow(TweezerSpot, cmap='viridis',vmin=np.amin(TweezerSpot) , vmax=np.amax(TweezerSpot) ) 
    plt.xlabel('Integrated Signal='+str(totphotons))
    save_imag(plt, 'region_fluo')
    plt.show() 


saving_script(path)
