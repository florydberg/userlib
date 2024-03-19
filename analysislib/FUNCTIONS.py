from lyse import *
from runmanager.remote import *
from pylab import *
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as patches
import matplotlib.gridspec as gridspec
from labscript.labscript import *
import analysislib
from scipy.optimize import curve_fit

def calculate_optical_density_fft(up, down):
    # Calculate optical density
    optical_density = -1 *np.log((up/down))

    # Compute the 2D Fourier Transform
    fft_result = np.fft.fft2(optical_density)
    fft_result_shifted = np.fft.fftshift(fft_result)

    # Get the dimensions of the image
    rows, cols = optical_density.shape
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
    im1 = plt.imshow(optical_density, cmap='viridis', vmin=0, vmax=0.2)
    plt.title('Original Image')
    plt.colorbar(im1, ax=plt.gca())

    plt.subplot(222)
    plt.imshow(np.log(1 + np.abs(fft_result_shifted)), cmap='gray')
    plt.title('2D Fourier Transform')

    # Apply the inverse process
    optical_density_FFT = np.fft.ifft2(np.fft.ifftshift(fft_result_lowpass)).real

    plt.subplot(223)
    plt.imshow(np.log(1 + np.abs(fft_result_lowpass)), cmap='gray')
    plt.title('Low-pass Filtered Fourier Transform')

    plt.subplot(224)
    im2 = plt.imshow(optical_density_FFT, cmap='viridis', vmin=0, vmax=0.2)
    plt.title('Image after Inverse Fourier Transform')
    plt.colorbar(im2, ax=plt.gca())

    plt.show()

    return optical_density, optical_density_FFT

def fit_gaussian(shot, data_frame, RX, RY, natoms, S, calibr, unity):
    # Define a 2D Gaussian function
    def gaussian_2d(xy, amplitude, xo, yo, sigma_x, sigma_y, th):
        theta = th * np.pi
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

    # Fit the 2D Gaussian to the image
    initial_guess = (100, 100, 100, 15, 15, 0.01)  # Initial guess for amplitude, xo, yo, sigma_x, sigma_y, theta
    low = [0, 0, 0, 5, 5, 0]
    upper = [float('inf'), float('inf'), float('inf'), RX, RY, 0.25]
    bounds = [low, upper]
    popt, _ = curve_fit(gaussian_2d, (X, Y), natoms.ravel(order='F'), p0=initial_guess, bounds=bounds)

    # Extract the parameters
    amplitude, xo, yo, sigma_x, sigma_y, theta = popt

    # Print the fitted parameters
    print("Amplitude:", amplitude)
    print("Center (x, y):", xo, RY - yo)
    print("Standard Deviations (sigma_x, sigma_y):", sigma_x, sigma_y)
    print("Theta: %s pi " % (round(theta * 100) / 100))

    # Generate the fitted Gaussian distribution
    fit_data = gaussian_2d((X, Y), *popt)
    fitdata = fit_data.reshape((RY, RX), order='F')

    fitN_of_atoms = np.sum(fitdata)
    print('\n----------------------------------------\n\nGauss-Fitted Number of atoms = %s 10^6' % (round(fitN_of_atoms / 10000) / 100))
    print('\n----------------------------------------\n')

    density = amplitude / S * 1e-8  # in cm^2

    #########################  Plot the original data and the fitted Gaussian  ####################
    figure()
    plt.figure(figsize=(20, 10))
    # 2d image plot with profiles
    h, w = natoms.shape
    h = h * 2
    w = w * 2

    gs = gridspec.GridSpec(3, 3, width_ratios=[w * .2, w, w], height_ratios=[h * .2, h, h * .2])

    ax = [plt.subplot(gs[3]), plt.subplot(gs[4]), plt.subplot(gs[7]), plt.subplot(gs[5])]
    bounds = [x.min(), x.max(), y.min(), y.max()]

    ax[1].imshow(natoms, cmap='viridis', vmin=0, vmax=50, extent=(x.min(), x.max(), y.min(), y.max()))

    inty = np.sum(natoms, axis=1)
    gauy = np.sum(fitdata, axis=1)
    ax[0].plot(inty[::-1], np.linspace(1, inty.shape, 250), 'b')
    ax[0].plot(gauy[::-1], np.linspace(1, inty.shape, 250), 'r')

    intx = np.sum(natoms, axis=0)
    gaux = np.sum(fitdata, axis=0)
    ax[2].plot(intx, 'b')
    ax[2].plot(gaux, 'r')

    name = str('Number of atoms = %s 10^6' % (round(fitN_of_atoms / 10000) / 100))
    plt.title(name)
    picname = "FitAtoms@" + str(data_frame[calibr]) + unity + calibr + ".png"
    plt.xlabel(str('peak density: %s 10^4 atoms in cm^2\n theta=%s pi \n sigma_x, sigma_y:(%s, %s)\n Center=(%s, %s) \n %s' %
                (round(density / 100) / 100, round(theta * 100) / 100, round(sigma_x * 100) / 100,
                    round(sigma_y * 100) / 100,
                    round(xo * 100) / 100, round((RY - yo) * 100) / 100, str(picname))))
    ax[3].imshow(fitdata, cmap='viridis', vmin=0, vmax=50, extent=(x.min(), x.max(), y.min(), y.max()))

    plt.savefig(picname)
    main_waist = sigma_x

    plt.show()

    shot.save_result('number_of_atoms', fitN_of_atoms)
    shot.save_result('peak_density', density)
    shot.save_result('main_waist', main_waist)
    print('fitted results saved')

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

def get_OD_coefficent(data_frame, img):  # Constants and Image Analysis  
    Img_frq=data_frame['Imaging_Frq']
    Imag_beam_Power=440e-6 #W   #TODO: update this value with the measure we have to take

    Waist2=0.006667*0.006667 #m
    Isat=67.6
    sat=2*Imag_beam_Power/np.pi/Waist2/Isat #TODO: check this eq
    print('saturation = '+ str(round(sat*100)/100))   
    image_size = img[str('Atoms')].shape
    absorption_coefficient = 0.02 
    pixel_size = 1.85e-6  # micrometers per pixel
    atom_mass = 1.67*88e-27  # mass of a single atom (in kilograms)
    pix=pixel_size*500/150 # effective pixel size
    pixArea=pix*pix #pixArea = Sat
    sigma=9.7e-14 
    lam = 461*1e-9
    delta=0
    Gam=32e6
    sig=3*lam**2/2/np.pi*(1/(1+(2*delta/Gam)**2))*1/(1+sat) #TODO: check this eq
    print('sigma = '+ str(sig))
    return pixArea,sig

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

def plot_up_down(up, down, data_frame, calibr, unity, P0, RX, RY):    
    plt.figure()
    MOT1=patches.Rectangle(P0, RX, RY, linewidth=1, edgecolor='r', facecolor='none')    
    plt.imshow(up-down, cmap='viridis')
    plt.gca().add_patch(MOT1)
    plt.colorbar()
    plt.legend(['Atoms'], loc ="lower right")
    plt.title('Up-Down @'+str(data_frame[calibr])+unity+calibr)
    plt.show()