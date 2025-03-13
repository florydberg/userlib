from lyse import *
from runmanager.remote import *
from pylab import *
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as patches
import matplotlib.gridspec as gridspec
import runmanager
import random

data_frame = data()
plotting=1
seq_index=data_frame['sequence_index']

######################################################################################

path=data_frame['filepath'].iloc[-1] #lastvalue in dataframe
print(path)

TOF=data_frame['TOF'].iloc[-1]
print('Time of Flight = ', int(TOF), 'ms' )


with Run(path).open('r+') as shot:
    j=0
    img={}
    for i in ['Atoms', 'Probe', 'Background']:

        # Obtaining multiple images and averaging them:
        shot_image=shot.get_image('Basler_Camera',str(i),'tiff')
        if int(data_frame['n_loop'].iloc[0])>1:
            img[str(i)] = np.average(shot_image.astype(np.float32),axis=0)
        else:
            img[str(i)]=shot_image.astype(np.float32)

        if True:#ROI Selection
            P0=(250,250)   # Starting point for the atoms ROI
            RX=250
            RY=250

            DX=(P0[0], P0[0]+RX)
            DY=(P0[1], P0[1]+RY)

            MOT=patches.Rectangle(P0, RX, RY, linewidth=1, edgecolor='r', facecolor='none') 

            p0=(150,100)   # Starting point for the correction area 
            rX=300
            rY=100

            dX=(p0[0], p0[0]+rX)
            dY=(p0[1], p0[1]+rY)

            corr=patches.Rectangle(p0, rX, rY, linewidth=1, edgecolor='b', facecolor='none')

            b0=(320,310)    # Starting point for the Probe area
            ray=270
            BEAM=patches.Circle(b0, ray, linewidth=1, edgecolor='y', facecolor='none')       
        if plotting:
            plt.figure(j+1)
            plt.gca().add_patch(MOT)
            plt.gca().add_patch(corr)
            plt.gca().add_patch(BEAM)
            plt.title(str(i))
            plt.imshow(img[str(i)])
            plt.colorbar()
            plt.show()       
        j+=1

    if True:  # Constants and Image Analysis  
        Img_frq=114.0 #MHz
        Imag_beam_Power=440e-6 #W

        Waist2=0.006667*0.006667 #m
        Isat=67.6
        sat=2*Imag_beam_Power/np.pi/Waist2/Isat
        sat=round(sat*100)/100
        print('saturation = '+ str(sat))   

        image_size = img[str(i)].shape
        absorption_coefficient = 0.02
        pixel_size = 1.85e-6  # micrometers per pixel
        atom_mass = 1.67*88e-27  # mass of a single atom (in kilograms)
        pix=pixel_size*500/150 # effective pixel size
        S=pix*pix
        sigma=9.7e-14
        lam = 461*1e-9
        delta=1
        Gam=1
        sig=3*lam**2/2/np.pi*(1/(1+(2*delta/Gam)**2))*1/(1+sat)
        print('sigma = '+ str(sig))

    # Calculate the optical density
    up=(img['Atoms']-img['Background'])
    print('Image dimensions = '+ str(up.shape))
    down=(img['Probe']-img['Background'])

    down[down<=1] = 1  # why 1 and not just 0?
    up[up<=1] = 1

    Ia=np.sum(up[np.ix_(range(dY[0],dY[1]),range(dX[0],dX[1]))])
    Ib=np.sum(down[np.ix_(range(dY[0],dY[1]),range(dX[0],dX[1]))])
    intensity_correction=Ia/Ib
    if plotting:
        plt.figure(j+1)
        plt.imshow(up-down, cmap='viridis')
        plt.colorbar()
        plt.title('Up-Down')
        plt.show()

    optical_density = -1 *np.log((up/down)/intensity_correction)
    OD=optical_density[np.ix_(range(DY[0],DY[1]),range(DX[0],DX[1]))]
    if plotting:
        plt.figure(j+2)
        plt.imshow(OD, cmap='viridis', vmin=0, vmax=0.35 )
        plt.colorbar()
        plt.title('Optical Density')
        plt.show()
    natoms = S/sigma*OD
    number_of_atoms = np.sum(natoms) # Total number of atoms in the cloud
    print('atoms', number_of_atoms )
    print(f"First-guessed number of atoms in the cloud: {number_of_atoms:.2e}")

    if True: ##FITTING on GAUSSIAN
        from scipy.optimize import curve_fit

        # Define a 2D Gaussian function
        def gaussian_2d(xy, amplitude, xo, yo, sigma_x, sigma_y, th):
            theta=th*np.pi
            x, y = xy
            xo = float(xo)
            # xo=30
            yo = float(yo)
            a = (np.cos(theta)**2) / (2 * sigma_x**2) + (np.sin(theta)**2) / (2 * sigma_y**2)
            b = -(np.sin(2 * theta)) / (4 * sigma_x**2) + (np.sin(2 * theta)) / (4 * sigma_y**2)
            c = (np.sin(theta)**2) / (2 * sigma_x**2) + (np.cos(theta)**2) / (2 * sigma_y**2)
            return amplitude * np.exp(-(a * (x - xo)**2 + 2 * b * (x - xo) * (y - yo) + c * (y - yo)**2))

        x = np.linspace(1, RX, RX)
        y = np.linspace(1, RY, RY)
        xx, yy = np.meshgrid(x, y)
        X=xx.ravel(order='F')
        Y=yy.ravel(order='F')

        ## DATA CORRECTION:
        # natoms[natoms<200]=0


        # Fit the 2D Gaussian to the image
        initial_guess = (1000, 35, 35, 15, 15, 0.25)  # Initial guess for amplitude, xo, yo, sigma_x, sigma_y, theta
        low=[0,0,0,5,5,0]
        upper=[float('inf'),float('inf'),float('inf'),RX,RY,0.50]
        bounds=[low, upper]
        popt, _ = curve_fit(gaussian_2d, (X,Y), natoms.ravel(order='F'), p0=initial_guess, bounds=bounds)

        # Extract the parameters
        amplitude, xo, yo, sigma_x, sigma_y, theta = popt


        # Print the fitted parameters
        print("Amplitude:", amplitude)
        print("Center (x, y):", xo, RY-yo)
        print("Standard Deviations (sigma_x, sigma_y):", sigma_x, sigma_y)
        print("Theta: %s pi " %(round(theta*100)/100) )

        # Generate the fitted Gaussian distribution
        fit_data = gaussian_2d((X,Y), *popt)
        fitdata=fit_data.reshape((RY,RX), order='F')

        fitN_of_atoms = np.sum(fitdata)
        print('\n----------------------------------------\n\nGauss-Fitted Number of atoms = %s 10^6'%(round(fitN_of_atoms/10000)/100))
        print('\n----------------------------------------\n')

        density=amplitude/S*1e-8 #in cm^2

        #########################  Plot the original data and the fitted Gaussian  ####################

        plt.show()

        gs = gridspec.GridSpec(1, 3)

        fig=plt.figure()

        ax1=plt.subplot(gs[0])
        name=('Atoms')
        plt.title(name)
        ax1.imshow(img['Atoms'], cmap='viridis',  extent=(x.min(), x.max(), y.min(), y.max()))
        plt.show()

        ax2=plt.subplot(gs[1])
        name=('Probe')
        plt.title(name)
        ax2.imshow(img['Probe'], cmap='viridis',  extent=(x.min(), x.max(), y.min(), y.max()))

        ax3=plt.subplot(gs[2])
        name=('Background')
        plt.title(name)
        ax3.imshow(img['Background'], cmap='viridis',  extent=(x.min(), x.max(), y.min(), y.max()))

        if plotting:
            plt.show()

        ##################################################################################################

        figure(10)
        plt.figure(figsize=(20, 10))
        # 2d image plot with profiles
        h, w = natoms.shape
        h=h*2
        w=w*2

        gs = gridspec.GridSpec(3, 3,width_ratios=[w*.2,w,w], height_ratios=[h*.2,h,h*.2])

        ax = [plt.subplot(gs[3]),plt.subplot(gs[4]),plt.subplot(gs[7]),  plt.subplot(gs[5])]
        bounds = [x.min(),x.max(),y.min(),y.max()]

        ax[1].imshow(natoms, cmap='viridis', vmin=-100, vmax=3000, extent=(x.min(), x.max(), y.min(), y.max()))

        inty=np.sum(natoms,axis=0)
        gauy=np.sum(fitdata, axis=0)
        ax[0].plot(inty, np.linspace(1,inty.shape, 250), 'b')
        ax[0].plot(gauy, np.linspace(1,inty.shape, 250) , 'r')

        intx=np.sum(natoms,axis=1)
        gaux=np.sum(fitdata, axis=1)
        ax[2].plot(intx, 'b')
        ax[2].plot(gaux, 'r')
        
        name=str('Number of atoms = %s 10^6'%(round(fitN_of_atoms/10000)/100)) 
        plt.title(name)
        plt.xlabel(str('peak density: %s 10^4 atoms in cm^2\n theta=%s pi \n sigma_x, sigma_y:(%s, %s)\n Center=(%s, %s)' 
                    %(round(density/100)/100, round(theta*100)/100, round(sigma_x*100)/100, round(sigma_y*100)/100, 
                    round(xo*100)/100, round((RY-yo)*100)/100)))
        ax[3].imshow(fitdata, cmap='viridis', vmin=-100, vmax=3000, extent=(x.min(), x.max(), y.min(), y.max()))

        if plotting:
            plt.show()
    shot.save_result('number_of_atoms', number_of_atoms)
    print('results saved')
