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
from scipy.ndimage import gaussian_filter, label, center_of_mass
import time # for testing speed of program
import datetime, time
ts=time.time()
datetime.datetime.now()
dt=datetime.datetime.now().date()


from lyse import *
from pylab import *
import csv
import runmanager
from runmanager.remote import *
import numpy as np
import math
from scipy.optimize import curve_fit, least_squares
from scipy.stats import poisson
import numpy as np
import matplotlib.pyplot as plt
import datetime, time
import seaborn as sns
import pandas as pd
from scipy.special import erf
ts=time.time()
dt=datetime.datetime.now().date()

def saturation(dBm):
        Imag_beam_Power=140e-6/28*dBm #W   #TODO: update this value with the measure we have to take

        waist_0=6.667e-3 #m
        I=2*Imag_beam_Power/(np.pi*waist_0**2)
        lambda_laser = 461*1e-9
        delta=0
        Gam=32e6

        h=6.626e-34 #JHz^-1
        c=2.99e8 # m/s

        I_sat = (np.pi* h*c*Gam)/(3*lambda_laser**3) # previous calculation was 67.6
        sat=I*100000//I_sat/100000
        # sat=I/I_sat
        return sat

def data_mean(para, values):
    data1 = {}
    std1 = {}
    stdN = {}
    for ii in set(para):
        indices = [idx for idx, val in enumerate(para) if val == ii]
        aa = [values[idx] for idx in indices]
        data1[ii] = np.mean(aa)
        std1[ii] = np.std(aa)
        stdN[ii] = np.std(aa)/sqrt(len(aa))
    x = sorted(data1.keys())
    y = [data1[key] for key in x]
    e = [std1[key] for key in x]
    eN= [stdN[key] for key in x]
    return x, y, e, eN

def duo_mean(param1, param2, values):
    """
    Computes the mean, standard deviation, and standard error for each combination of param1 and param2 values.

    Args:
        param1: List or array of first parameter values.
        param2: List or array of second parameter values.
        values: List or array of values corresponding to the param1, param2 pairs.

    Returns:
        A dictionary containing:
        - mean_values: Dictionary with (param1, param2) pairs as keys and their mean values as values.
        - std_values: Dictionary with (param1, param2) pairs as keys and their standard deviations as values.
        - error_values: Dictionary with (param1, param2) pairs as keys and their standard errors as values.
    """
    mean_values = {}
    std_values = {}
    error_values = {}
    
    # Ensure that param1, param2, and values are all of the same length
    if len(param1) != len(param2) or len(param1) != len(values):
        raise ValueError("The length of param1, param2, and values must be the same.")

    # Create unique pairs of (param1, param2)
    unique_pairs = set(zip(param1, param2))
    
    for pair in unique_pairs:
        # Step 1: Generate indices where param1 and param2 match the pair
        indices = [idx for idx, val in enumerate(zip(param1, param2)) if val == pair]

        if not indices:
            continue  # Skip if there are no indices for this pair
        
        # Step 2: Extract corresponding values using indices
        try:
            aa = [values[idx] for idx in indices]
        except IndexError as e:
            print(f"IndexError: {e}. Check the length of the values list and the indices.")
            continue
        
        # Step 3: Compute mean, std, and error on mean
        mean_values[pair] = np.mean(aa)
        std_values[pair] = np.std(aa)
        error_values[pair] = np.std(aa) / sqrt(len(aa))
    
    return mean_values, std_values, error_values

def plot_heatmap(mean_values):
    """
    Plots a heatmap from the mean values of (param1, param2) pairs.

    Args:
        mean_values: Dictionary with (param1, param2) pairs as keys and their mean values as values.
    """
    # Step 1: Convert the mean_values dictionary to a DataFrame
    df = pd.DataFrame(list(mean_values.items()), columns=['Params', 'Mean Value'])
    
    # Split the Params tuple into two separate columns: 'param1' and 'param2'
    df['param1'] = df['Params'].apply(lambda x: x[0])
    df['param2'] = df['Params'].apply(lambda x: x[1])
    
    # Step 2: Pivot the DataFrame to create a matrix format
    df_pivot = df.pivot(index='param1', columns='param2', values='Mean Value')

    # Step 3: Plot the heatmap
    plt.figure(figsize=(8, 6))
    sns.heatmap(df_pivot, annot=False, fmt='.0f', cmap="viridis", linewidths=.5, vmin=0, vmax=+2500)
    
    # Add labels and a title
    plt.title("Heatmap of Mean Values across param1 and param2")
    plt.xlabel("param2")
    plt.ylabel("param1")
    
    plt.show()

def save_imag(plt, name):
    picname = name
    if duo:
        img_name=str(dt) + '_' + str(datetime.datetime.now().hour) + str(datetime.datetime.now().minute) + str(datetime.datetime.now().second)  + '_' + para1_name + '_' + para2_name
    else:
        img_name=str(dt)  + '_' + str(datetime.datetime.now().hour)+ str(datetime.datetime.now().minute) +  str(datetime.datetime.now().second)  + '_' + para1_name
    plt.savefig(two_levels_up+ '/' + img_name +  '_' + picname + ".png")
    print(picname + ' saved')

def Tweezers_scan(value, title):
    plt.figure()  ##################################################################### 
    for jj in range(9):
        means_ii=tuple(value.get(str(jj+1)))
        x,y,error,errorN=data_mean(parameter1, means_ii)
        # Subtract offset from x-axis values
        x_adjusted = [2*(xi) for xi in x]
        # plt.errorbar(x, y, yerr=errorN, fmt='--o', ecolor='gray',capsize=5)
        plt.errorbar(x, y, yerr=errorN, fmt='--o', ecolor='gray',capsize=5)  #
    plt.rcParams.update({'font.size': 20})
    plt.legend(['ROI1','ROI2','ROI3','ROI4','ROI5','ROI6','ROI7','ROI8','ROI9'])
    xlabel=str(para1_name)+' ('+str(para1_unit)+')'
    if saving_location:
        xlabel+='\n'+ str(one_level_up)
    # plt.xlabel(xlabel)
    plt.xlabel('Detuning from free space resonance (MHz)')
    #plt.xlabel('time(ms) holdTime_fluoImg')
    plt.title(str(one_level_up))
    plt.ylabel('photons')
    # plt.yscale('log')
    plt.grid(True)
    # plt.xscale('log')
    # plt.ylim(0,1)
    if saving_plots: save_imag(plt, title)  #####################################################################


def Tweezers_scan_tot(value, title):
    plt.figure()  ##################################################################### 
    all_y = []
    all_errorN = []    
    
    for jj in range(9):
        means_ii=tuple(value.get(str(jj+1)))
        x,y,error,errorN=data_mean(parameter1, means_ii)
                
        all_y.append(y)
        all_errorN.append(errorN)

    all_y = np.array(all_y)  
    all_errorN = np.array(all_errorN)

    y_mean = np.mean(all_y, axis=0)  
    errorN_mean = np.sqrt(np.sum(all_errorN**2, axis=0)) / 9  

    # Subtract offset from x-axis values
    x_adjusted = [2*(xi) for xi in x]
    # plt.errorbar(x, y, yerr=errorN, fmt='--o', ecolor='gray',capsize=5)
    plt.errorbar(x, y_mean, yerr=errorN_mean, fmt='--o', ecolor='gray',capsize=5)  #
    plt.rcParams.update({'font.size': 20})
    # plt.legend(['mean of the 9 ROI'])
    # xlabel=str(para1_name)+' ('+str(para1_unit)+')'
    # if saving_location:
        # xlabel+='\n'+ str(one_level_up)
    # plt.xlabel(xlabel)
    plt.xlabel('Detuning from free space resonance (MHz)')
    #plt.xlabel('time(ms) holdTime_fluoImg')
    plt.title(str(one_level_up))
    plt.ylabel('photons')
    # plt.yscale('log')
    plt.grid(True)
    # plt.xscale('log')
    # plt.ylim(0,1)
    # if saving_plots: save_imag(plt, title)  #####################################################################


def Tweezers_scan_duo(values, title):
    values=tuple(values)
    mean_values, std_values, error_values = duo_mean(parameter2, parameter1, values)
    plot_heatmap(mean_values)

    plt.ylabel(str(para2_name)+ ' ('+str(para2_unit)+')')
    xlabel=str(para1_name)+' ('+str(para1_unit)+')'
    if saving_location:
        xlabel+='\n' + str(one_level_up)
    plt.xlabel(xlabel)
    plt.title(title)

    print("Heatmap data saved to heatmap_data.csv")

    if saving_plots: save_imag(plt, title)  #####################################################################

################################### 
duo=0
saturation_conversion=False
saving_plots=True
saving_location=True
# n_tweezer=3
# n_tweezer=5
n_tweezer=9

para1_name='Sisyphus_Frq' #'n_shot'
para1_unit='MHz'    #'s' 
if duo:
    para2_name='FluoImgPulse_Dt'
    para2_unit='ms'

###################################

try: #initialization
    df = data()
    second_shot = all(pd.Series.to_list(df['second_shot']))
    paths=df['filepath']
    FluoAnalyser= df['FluoAnalyser_5tweez']
    # FluoAnalyser= df['FluoAnalyser_TWEEZERS']
    means={}
    maxs={}
    vars={}
    photons={}
    atoms={}
    
    parameter1=np.array(df[para1_name])
    if duo:
        parameter2=np.array(df[para2_name])

    for ii in range(0,n_tweezer):
        mean_name='mean_tweezer_'+str(ii+1)
        means[str(ii+1)]=tuple(FluoAnalyser[mean_name])
        mm=tuple(FluoAnalyser[mean_name])

        max_name='mean_tweezer_'+str(ii+1)
        maxs[str(ii+1)]=tuple(FluoAnalyser[max_name])
        mxm=tuple(FluoAnalyser[max_name])

        var_name='variance_tweezer_'+str(ii+1)
        vars[str(ii+1)]=(tuple(FluoAnalyser[var_name]))
        vv=tuple(FluoAnalyser[var_name])

        photon_name='photon_tweezer_'+str(ii+1)
        photons[str(ii+1)]=(tuple(FluoAnalyser[photon_name]))
        pp=tuple(FluoAnalyser[photon_name])

        atom_in_name='atom_in_tweezer_'+str(ii+1)
        atoms[str(ii+1)]=(tuple(FluoAnalyser[atom_in_name]))
        aa=tuple(FluoAnalyser[atom_in_name])
     
    if second_shot:
        for ii in range(n_tweezer+1,2*n_tweezer+1):
            mean_name='mean_tweezer_'+str(ii+1)
            means[str(ii+1)]=tuple(FluoAnalyser[mean_name])
            mm=tuple(FluoAnalyser[mean_name])

            max_name='mean_tweezer_'+str(ii+1)
            maxs[str(ii+1)]=tuple(FluoAnalyser[max_name])
            mxm=tuple(FluoAnalyser[max_name])

            var_name='variance_tweezer_'+str(ii+1)
            vars[str(ii+1)]=(tuple(FluoAnalyser[var_name]))
            vv=tuple(FluoAnalyser[var_name])

            photon_name='photon_tweezer_'+str(ii+1)
            photons[str(ii+1)]=(tuple(FluoAnalyser[photon_name]))
            pp=tuple(FluoAnalyser[photon_name])

            atom_in_name='atom_in_tweezer_'+str(ii+1)
            atoms[str(ii+1)]=(tuple(FluoAnalyser[atom_in_name]))
            aa=tuple(FluoAnalyser[atom_in_name])

    photo_background=tuple(FluoAnalyser['photo_background'])
    photo_background_2nd=tuple(FluoAnalyser['photo_background_2nd'])

    if saturation_conversion:
        if para1_name=='ImagingFluo_Pow': # conversion dbm to saturation parameter:
            parameter1=saturation(parameter1)
            para1_name='Saturation_Parameter'
            para1_unit='s'
        elif duo:
            if para2_name=='ImagingFluo_Pow': # conversion dbm to saturation parameter:
                parameter2=saturation(parameter2)
                para2_name='Saturation_Parameter'
                para2_unit='s'

    if True: #print list of shots in the characterization
        if duo:
            list_name=str(dt)  + '_' + str(datetime.datetime.now().hour)+ str(datetime.datetime.now().minute) +  str(datetime.datetime.now().second)  + '_' + para1_name + '_' + para2_name
        else:
            list_name=str(dt)  + '_' + str(datetime.datetime.now().hour)+ str(datetime.datetime.now().minute) +  str(datetime.datetime.now().second)  + '_' + para1_name
        list_path=paths[-1]
        one_level_up = os.path.dirname(list_path)
        two_levels_up = os.path.dirname(one_level_up)
        print(two_levels_up)


        file_name=list_name+'.csv'

        with open(two_levels_up+ '/' + file_name, 'a', newline='') as csv_file:
            writer = csv.writer(csv_file)
            for ii in paths:
                # print(ii)
                writer.writerow([ii])

    ###################################
    if duo:
        print('duo analysis')
        for ii in range(n_tweezer):
            Tweezers_scan_duo(photons[str(ii+1)],'Photons from Tweezer '+ str(ii+1))
            img_name=str(dt) + '_' + str(datetime.datetime.now().hour) + str(datetime.datetime.now().minute) + str(datetime.datetime.now().second)  
            img_name+='_' + para1_name + '_' + para2_name + '_tweezer_'+str(ii+1)
            df.to_csv(two_levels_up+ '/' + img_name + '.csv', index=False)
    else:
        print('single analysis')
        # Tweezers_scan(atoms, 'Occupation 0-1 in the tweezers')
        Tweezers_scan(photons, 'Photo-Count of Fluo Signal')



    with Run(path).open('r') as shot:
    
        def load_images_from_lyse(df, shot, include_second_shot=False):
            images = []

            fluo_img = shot.get_image('Orca_Camera', 'TweezFluo', 'frame')
            if int(df['n_loop']) > 1:
                images.append(np.average(fluo_img.astype(np.float32), axis=0))
            else:
                images.append(fluo_img.astype(np.float32))

            if include_second_shot and df['second_shot']:
                fluo_2 = shot.get_image('Orca_Camera', 'second-shot', 'frame')
                if int(df['n_loop']) > 1:
                    images.append(np.average(fluo_2.astype(np.float32), axis=0))
                else:
                    images.append(fluo_2.astype(np.float32))

            return np.mean(images, axis=0)

        
        pixel_size = 4.6e-6
        magnification = 4.083
        effective_pixel_size = pixel_size / magnification

        def find_atom_positions(mean_image, threshold_std=3, smoothing_sigma=1):
            smoothed = gaussian_filter(mean_image, sigma=smoothing_sigma)
            threshold = np.mean(smoothed) + threshold_std * np.std(smoothed)
            mask = smoothed > threshold
            labeled, num_features = label(mask)
            pixel_positions = center_of_mass(smoothed, labeled, range(1, num_features + 1))
            micron_positions = [(y * effective_pixel_size * 1e6, x * effective_pixel_size * 1e6) for y, x in pixel_positions]
            return pixel_positions, micron_positions

        def plot_mean_image(mean_image, atom_positions=None, title='Mean Fluorescence Image'):
            plt.figure(figsize=(8, 8))
            plt.imshow(mean_image, cmap='plasma')
            plt.colorbar(label='Counts')
            plt.title(title)
            plt.xlabel('Pixels')
            plt.ylabel('Pixels')
            if atom_positions:
                for y, x in atom_positions:
                    plt.plot(x, y, 'wo', markersize=6, markerfacecolor='none', markeredgewidth=1.5)
            plt.tight_layout()
            plt.show()

        
        include_second = True
        mean_img = load_images_from_lyse(df, shot, include_second_shot=include_second)
        pixel_coords, micron_coords = find_atom_positions(mean_img, threshold_std=3)

        print("Atomi trovati (in micron):", micron_coords)
        plot_mean_image(mean_img, atom_positions=pixel_coords)


except:
    pass





