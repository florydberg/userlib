from lyse import *
from runmanager.remote import *
from pylab import *
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as patches
import matplotlib.gridspec as gridspec
from labscript.labscript import *
import analysislib
from scipy.optimize import curve_fit, least_squares
import time # for testing speed of program
def bin_data(data, bin_size):
    shape = data.shape
    new_shape = (shape[0] // bin_size, bin_size, shape[1] // bin_size, bin_size)
    binned_data = data.reshape(new_shape).sum(axis=(1, 3)) / (bin_size**2)
    return binned_data

if True: #functions definition
    if True:  # Constants and Image Analysis  
        V_MAX=0.15

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
    
    def fit_gaussian(shot, value, RX, RY, data, scan_parameter, scan_unit, binfactor):
        # Define a 2D Gaussian function
        def gaussian_2d(xy, amplitude, xo, yo, sigma_x, sigma_y, theta):
            theta = theta * np.pi
            x, y = xy
            xo = float(xo)
            yo = float(yo)
            a = (np.cos(theta)**2) / (2 * sigma_x**2) + (np.sin(theta)**2) / (2 * sigma_y**2)
            b = -(np.sin(2 * theta)) / (4 * sigma_x**2) + (np.sin(2 * theta)) / (4 * sigma_y**2)
            c = (np.sin(theta)**2) / (2 * sigma_x**2) + (np.cos(theta)**2) / (2 * sigma_y**2)
            return amplitude * np.exp(-(a * (x - xo)**2 + 2 * b * (x - xo) * (y - yo) + c * (y - yo)**2))

        x = np.linspace(1, RX, RX)
        y = np.linspace(1, RY, RY)
        xx, yy = np.meshgrid(x, y)
        X = xx.ravel(order='F')
        Y = yy.ravel(order='F')
        xy = (X, Y)

        inty = np.sum(data, axis=1)
        intx = np.sum(data, axis=0)
        ampguess=10# min([np.max(data),np.max(intx)/(2*np.pi)**(1/2),np.max(inty)/(2*np.pi)**(1/2)])
        
        # Fit the 2D Gaussian to the image
        
        initial_guess = (ampguess, RX/2, RY/2, 85, 85, 0.01)  # Initial guess for amplitude, xo, yo, sigma_x, sigma_y, theta
        low = [0, 0, 0, 5, 5, 0]
        upper = [1e10, RX, RY, RX, RY, 0.25]
        bounds = [low, upper]
        print("dfsdgfsdgsdgds ",initial_guess)

        def residuals(params, xy, data):
            return gaussian_2d(xy, *params) - data

        #popt, _ = curve_fit(gaussian_2d, (X, Y), data.ravel(order='F'), p0=initial_guess, bounds=bounds)

        # Extract the parameters
        data_ravel = data.ravel(order='F')
        result = least_squares(residuals, initial_guess, bounds=bounds, args=(xy, data_ravel), method='trf')
        popt = result.x

        # Extract parameter


        amplitude, xo, yo, sigma_x, sigma_y, theta = popt

        Npeak = amplitude * pixArea * binfactor**2 / sigma

        # Print the fitted parameters
        print("Npeak:", Npeak)
        print("Center (x, y):", xo, RY - yo)
        print("Standard Deviations (sigma_x, sigma_y):", sigma_x, sigma_y)
        print("Theta: %s pi " % (round(theta * 100) / 100))


        # Generate the fitted Gaussian distribution
        fit_data = gaussian_2d((X, Y), *popt)
        fitdata = fit_data.reshape((RY, RX), order='F')

        fitN_of_atoms = np.sum(fitdata*pixArea*binfactor**2/sigma)
        print('\n----------------------------------------\n\n Gauss-Fit-Summed Number of atoms = %s 10^6' % (round(fitN_of_atoms / 10000) / 100))
        print('\n----------------------------------------\n')

        #########################  Plot the original data and the fitted Gaussian  ####################
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
        # print(sigma_x)
        # print(fitN_of_atoms)
        # print(sigma_y)
        # print(n_3D)

        ax[3].imshow(fitdata, cmap='viridis', vmin=0, vmax=V_MAX, extent=(x.min(), x.max(), y.min(), y.max())) 
        plt.title('Fitted number of atoms = {}'.format("{:.2e}".format(fitN_of_atoms)))
        picname = " @ " + str(value) +' '+ scan_unit +' of '+ scan_parameter
        plt.xlabel(str('3D peak density: %s in cm$^3$  \n sig_x, sig_y:(%s um, %s um)\n Center=(%s, %s)\n theta=%s pi \n %s' %
                    ("{:.2e}".format(n_3D), "{:.0e}".format(sigma_x*1e6), "{:.2e}".format(sigma_y*1e6),
                        round(xo * 100) / 100, round((RY - yo) * 100) / 100, round(theta * 100) / 100, str(picname))))

        # plt.colorbar()
        plt.savefig(picname + ".png")
        avg_waist = (sigma_x+sigma_y)/2

        plt.show()

        shot.save_result('number_of_atoms', fitN_of_atoms)
        shot.save_result('peak_density', n_3D)
        shot.save_result('avg_waist', avg_waist)
        print('fitted results saved')

        print()

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

if True:# ROI Selection
    P0=(250,250)   # Starting point for the atoms ROI
    RX=600
    RY=600

    DX=(P0[0], P0[0]+RX)
    DY=(P0[1], P0[1]+RY)

    p0=(300,820)   # Starting point for the correction area 
    rX=200
    rY=80

    dX=(p0[0], p0[0]+rX)
    dY=(p0[1], p0[1]+rY)

    b0=(500,400)    # Starting point for the Probe area
    ray=400       
######################

scan_parameter='Red_MOT_Frq'
scan_unit='MHz'

op_plotting = False #extra images
op_FFTfilter = False
op_binning = True
op_gauss_fit = True
######################

with Run(path).open('r+') as shot:
    start_time = time.time()
    data_frame=data(path)
    j=0
    img={}
    for i in ['Atoms', 'Probe', 'Background']:

        MOT=patches.Rectangle(P0, RX, RY, linewidth=1, edgecolor='r', facecolor='none') 
        corr=patches.Rectangle(p0, rX, rY, linewidth=1, edgecolor='b', facecolor='none')
        BEAM=patches.Circle(b0, ray, linewidth=1, edgecolor='y', facecolor='none')
    
        shot_image=shot.get_image('Basler_Camera',str(i),'tiff')  # Obtaining multiple images and averaging them:
        if int(data_frame['n_loop'])>1: img[str(i)] = np.average(shot_image.astype(np.float32),axis=0)
        else: img[str(i)]=shot_image.astype(np.float32)

        if op_plotting: plot_single_image(MOT, corr, BEAM, img, i)
      
    figure()
    display_absorb_trio(img)

    up=(img['Atoms']-img['Background'])
    print('Image dimensions = '+ str(up.shape))
    down=(img['Probe']-img['Background'])

    # TODO optional place to put Fourier filtering on up and down

    down[down<=1] = 1 
    up[up<=1] = 1

    i_c=intensity_correction(up, down, dX, dY)
    print('intensity correction', i_c)
    down=down*i_c

    if op_plotting: plot_up_down(up, down, data_frame[scan_parameter], scan_parameter, scan_unit, P0, RX, RY)

    optical_density = -1 *np.log((up/down))
    if op_FFTfilter:
        optical_density = image_fft(optical_density)
    #OD = optical_density[np.ix_(range(DY[0],DY[1]),range(DX[0],DX[1]))
    OD = optical_density[np.ix_(range(DY[0],DY[1]),range(DX[0],DX[1]))]


    if op_plotting:
        plt.figure()
        plt.imshow(OD, cmap='viridis', vmin=0, vmax=0.2 )
        plt.colorbar()
        plt.title('Optical Density w/o Fringes')
        plt.show()

    n_2D = OD/sigma
    N_2D = n_2D*pixArea
    NN_2D=N_2D
    NN_2D[NN_2D<0]=0
    Ntot_sum = np.sum(NN_2D) # Total number of atoms in the cloud from images

    print('atoms', Ntot_sum )
    print(f"First-guess number of atoms in the cloud: {Ntot_sum:.2e}")
    shot.save_result('sum_of_atoms', Ntot_sum)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time:.6f} seconds")

    if op_gauss_fit:
        if op_binning:
            binfactor=4
            datafit= bin_data(OD, binfactor)
            RXfit=int(RX/binfactor)
            RYfit=int(RY/binfactor)
        else:
            datafit=OD
            binfactor=1
            RXfit=RX
            RYfit=RY
        fit_gaussian(shot, data_frame[scan_parameter], RXfit, RYfit, datafit, scan_parameter, scan_unit, binfactor)

    shot.save_result('scan_parameter', scan_parameter)
    shot.save_result('scan_unit', scan_unit)

saving_script(path)

