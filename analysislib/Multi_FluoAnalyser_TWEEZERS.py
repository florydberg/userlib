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
        plt.errorbar(x, y, yerr=errorN, fmt='--o', ecolor='black',capsize=5)  #
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
    plt.grid(False)
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
    print(x, y, errorN_mean)
    # plt.errorbar(x, y, yerr=errorN, fmt='--o', ecolor='gray',capsize=5)
    plt.errorbar(x, y_mean, yerr=errorN_mean, fmt='-o',mfc='none', mec='black', lw=1, ecolor='black', color='black', capsize=5)  #
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
    plt.grid(False)
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
################################### 
duo=0
saturation_conversion=False
saving_plots=True
saving_location=True
n_tweezer=9
saving_data=True

para1_name='ImagingFluo_SetPoint' #'n_shot'
para1_unit='ms'    #'s' 
if duo:
    para2_name='FluoImgPulse_Dt'
    para2_unit='ms'
################################### 
###################################

try: #initialization
# if True:
    df = data()
    second_shot = all(pd.Series.to_list(df['second_shot']))
    # second_shot=False
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
    
    if second_shot:
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
        if saving_data:
            histogram_data_csv = one_level_up + '/' + list_name +'histogram_data.csv'



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

    
    Tweezers_scan_tot(photons, 'Photo-Count of Fluo Signal')
    data_background=photo_background
    threshold = 20
    two_ph_threshold =  100#65
    nbin=50


    #Combined histogram for the whole array first shot

    plt.figure()
    # title='Histogram of Tweezer'
    title=str(one_level_up+'\n first shot')
    plt.title(title,fontsize=14)        
    data_background=photo_background
    # plt.xlim(-30,100)
    array_photons = np.concatenate([photons['1'],photons['2'],photons['3'],photons['4'],photons['5'],photons['6'],photons['7'],photons['8'],photons['9']]) 
    # array_photons = np.concatenate([photons['1'],photons['2'],photons['3']]) 
    countsG, binsG, _ = plt.hist([data_background, array_photons ] , bins=nbin, color=['b', 'r'  ]) #round(len(data_background)/5)
    if saving_data:
        with open(histogram_data_csv, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Histogram Type', 'Bin Center', 'Counts', 'Source'])
            for b, c in zip((binsG[:-1] + binsG[1:]) / 2, countsG[0]):
                writer.writerow(['Full Array - First Shot', b, c, 'BG'])
            for b, c in zip((binsG[:-1] + binsG[1:]) / 2, countsG[1]):
                writer.writerow(['Full Array - First Shot', b, c, 'Atoms'])
        print("Histogram data saved to:", histogram_data_csv)

    plt.legend(['BG','Atoms'])  #,
    #plt.axvline(x=threshold, color='red', linestyle='--')    
    #plt.axvline(x=two_ph_threshold, color='red', linestyle='--')  
    # Calculate the fraction of values above the threshold for the photon data
    total_photons = len(array_photons)
    # above_threshold = sum(1 for value in array_photons if value > threshold)
    # fraction = above_threshold / total_photons if total_photons > 0 else 0

    # above_threshold_values = array_photons[array_photons > threshold]
    above_threshold_values = array_photons[(array_photons > threshold) & (array_photons < two_ph_threshold)]
    fraction = len(above_threshold_values) / total_photons if total_photons > 0 else 0

    below_threshold_values = array_photons[array_photons <= threshold]

    mean_below = np.mean(below_threshold_values) if len(below_threshold_values) > 0 else 0
    std_below = np.std(below_threshold_values) if len(below_threshold_values) > 0 else 0
    mean_above = np.mean(above_threshold_values) if len(above_threshold_values) > 0 else 0
    std_above = np.std(above_threshold_values) if len(above_threshold_values) > 0 else 0


    # Annotate the fraction inside the plot
    plt.text(0.95, 0.65, f"Above Threshold: {fraction:.2%}",
        transform=plt.gca().transAxes, fontsize=12, ha='right', va='top',
        bbox=dict(boxstyle="round,pad=0.3", edgecolor="black", facecolor="white"))
    plt.text(0.95, 0.57, f"Mean Above: {mean_above:.2f}\nStd Above: {std_above:.2f}",
        transform=plt.gca().transAxes, fontsize=12, ha='right', va='top',
        bbox=dict(boxstyle="round,pad=0.3", edgecolor="black", facecolor="white"))
    plt.text(0.95, 0.45, f"Mean Below: {mean_below:.2f}\nStd Below: {std_below:.2f}",
        transform=plt.gca().transAxes, fontsize=12, ha='right', va='top',
        bbox=dict(boxstyle="round,pad=0.3", edgecolor="black", facecolor="white"))
    
    plt.xlabel('photons')
    plt.ylabel('occurencies')
    # plt.yscale('log')
    plt.show()

    #One histogram for each tweezer+threshold percentage first shot
    
    fig, ((ax1, ax2, ax3, ax4, ax5,ax6,ax7,ax8,ax9)) = plt.subplots(9, 1, figsize=(16, 26))

    # Define the axes in a list for easier iteration
    axes = [ax1, ax2, ax3, ax4, ax5,ax6,ax7,ax8,ax9]
    photon_keys = ['1', '2', '3', '4', '5','6','7','8','9']  # Corresponding photon keys
    titles = [f"ROI {i+1}" for i in range(9)]  # ROI labels
    
    for i, (ax, key, title) in enumerate(zip(axes, photon_keys, titles)):
        # Plot the histogram
        counts, bins, _ = ax.hist([data_background, photons[key]], bins=binsG, color=['b', 'r'])

        if saving_data:
            bin_centers = (bins[:-1] + bins[1:]) / 2
            with open(histogram_data_csv, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                for b, c in zip(bin_centers, counts[0]):
                    writer.writerow([f"ROI {i+1} - First Shot", b, c, 'BG'])
                for b, c in zip(bin_centers, counts[1]):
                    writer.writerow([f"ROI {i+1} - First Shot", b, c, 'Atoms'])


        ax.axvline(x=threshold, color='red', linestyle='--')
        ax.axvline(x=two_ph_threshold, color='red', linestyle='--')

        # Calculate the fraction of values above the threshold for the photon data
        total_photons = len(photons[key])
        above_threshold = np.sum(np.fromiter((1 for value in photons[key] if value > threshold), dtype=int))
        fraction = above_threshold / total_photons if total_photons > 0 else 0


        # Annotate the fraction inside the plot (in a framed box)
        ax.text(0.95, 0.95, f"Above Threshold: {fraction:.2%}", 
                transform=ax.transAxes, fontsize=12, ha='right', va='top',
                bbox=dict(boxstyle="round,pad=0.3", edgecolor="black", facecolor="white"))

        # Add ROI label next to each plot
        ax.text(-0.1, 0.5, title, 
                transform=ax.transAxes, fontsize=14, ha='right', va='center')

        
        ax.tick_params(axis='both', which='major', labelsize=12)  
        ax.tick_params(axis='both', which='minor', labelsize=10)
        if i < len(axes) - 1:
            ax.tick_params(axis='x', which='both',
                       bottom=False, top=False,
                       labelbottom=False, labelleft=False) # Rimuove l'etichetta dell'asse x (se presente)  
        axes[-1].set_xlabel("Photon Counts", fontsize=14)
    # plt.tight_layout()
    plt.show()
              
    # Calculate survival probability after Imaging
    if second_shot:    
        total_present = 0 
        loss = 0 # Atoms that were and are no longer there
        false_appearance = 0 # Atoms that were not there and appear later
        total_positions = 0

        for ii in range(1, n_tweezer+1):
            var_start = atoms[str(ii)]
            var_end = atoms[str(ii+ n_tweezer+1)]  #
                
            # for start, end in zip (var_start, var_end):
            #     if start == 1:
            #         total_pairs +=1
            #         if end == 0:
            #             loss += 1

            for start, end in zip(var_start, var_end):
                total_positions += 1
                if start == 1:
                    total_present += 1
                    if end == 0:
                        loss += 1
                elif start == 0 and end == 1:
                    false_appearance += 1


        
        survival = 1-loss / total_present if total_present > 0 else 0
        survival_error = np.sqrt(survival * (1 - survival) / total_present)
        stability = 1 - (loss + false_appearance) / total_positions if total_positions > 0 else 0
        print(f"Survival (atoms that remained): {survival:.2f}")
        print(f"False appearances (new atoms): {(false_appearance / total_positions):.2f}")
        print(f"Stability probability (no loss or new atom): {stability:.2f}")
        print(f"Survival (atoms that remained): {survival:.2f} ± {survival_error:.2f}")

        # Calcolo della survival probability individuale
        survival_per_tweezer = {}
        for ii in range(1, n_tweezer + 1):
            var_start = atoms[str(ii)]
            var_end = atoms[str(ii + n_tweezer + 1)]

            if len(var_start) != len(var_end):
                print(f"Warning: Tweezer {ii} has mismatched lengths between shots.")
                continue

            present = 0
            survived = 0

            for s, e in zip(var_start, var_end):
                if s == 1:
                    present += 1
                    if e == 1:
                        survived += 1

            if present > 0:
                survival_ratio = survived / present
            else:
                survival_ratio = float('nan')  # Nessun atomo iniziale, non si può definire

            survival_per_tweezer[ii] = survival_ratio

        print("\n--- Survival Probability per Tweezer ---")
        for t_id, prob in survival_per_tweezer.items():
            print(f"Tweezer {t_id}: {prob:.2f}")


        # surv_prob = 1- loss / total_pairs if total_pairs > 0 else 0

        # print(f"Survival probability: {surv_prob:.2f}")


               
    #Combined histogram for the whole array for the second shot
    if second_shot:
        plt.figure()
        title=str(one_level_up + '\n second shot')
        plt.title(title,fontsize=14)        
        data_background_2nd=photo_background_2nd
        # plt.xlim(-30,100)
        array_photons_2nd = np.concatenate([photons['11'],photons['12'],photons['13'],photons['14'],photons['15'],photons['16'],photons['17'],photons['18'],photons['19']])# 
        plt.hist([data_background_2nd, array_photons_2nd ] , bins=binsG, color=['b', 'r'  ]) #round(len(data_background)/5)
        if saving_data:
            bin_centers = (binsG[:-1] + binsG[1:]) / 2
            countsBG = np.histogram(data_background_2nd, bins=binsG)[0]
            countsAtoms = np.histogram(array_photons_2nd, bins=binsG)[0]
            with open(histogram_data_csv, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                for b, c in zip(bin_centers, countsBG):
                    writer.writerow(['Full Array - Second Shot', b, c, 'BG'])
                for b, c in zip(bin_centers, countsAtoms):
                    writer.writerow(['Full Array - Second Shot', b, c, 'Atoms'])

        plt.legend(['BG','Atoms'])  #,
        plt.axvline(x=threshold, color='red', linestyle='--')    
        plt.axvline(x=two_ph_threshold, color='red', linestyle='--')  
        # Calculate the fraction of values above the threshold for the photon data
        total_photons_2nd = len(array_photons_2nd)
        # above_threshold = sum(1 for value in array_photons if value > threshold)
        # fraction = above_threshold / total_photons if total_photons > 0 else 0

        # above_threshold_values = array_photons[array_photons > threshold]
        above_threshold_values_2nd = array_photons_2nd[(array_photons_2nd > threshold) & (array_photons_2nd < two_ph_threshold)]
        fraction_2nd = len(above_threshold_values_2nd) / total_photons_2nd if total_photons_2nd > 0 else 0

        below_threshold_values_2nd = array_photons_2nd[array_photons_2nd <= threshold]
    
        mean_below_2nd = np.mean(below_threshold_values_2nd) if len(below_threshold_values_2nd) > 0 else 0
        std_below_2nd = np.std(below_threshold_values_2nd) if len(below_threshold_values_2nd) > 0 else 0
        mean_above_2nd = np.mean(above_threshold_values_2nd) if len(above_threshold_values_2nd) > 0 else 0
        std_above_2nd = np.std(above_threshold_values_2nd) if len(above_threshold_values_2nd) > 0 else 0


        # Annotate the fraction inside the plot
        plt.text(0.95, 0.65, f"Above Threshold: {fraction_2nd:.2%}",
        transform=plt.gca().transAxes, fontsize=12, ha='right', va='top',
        bbox=dict(boxstyle="round,pad=0.3", edgecolor="black", facecolor="white"))
        plt.text(0.95, 0.57, f"Mean Above: {mean_above_2nd:.2f}\nStd Above: {std_above_2nd:.2f}",
        transform=plt.gca().transAxes, fontsize=12, ha='right', va='top',
        bbox=dict(boxstyle="round,pad=0.3", edgecolor="black", facecolor="white"))
        plt.text(0.95, 0.45, f"Mean Below: {mean_below_2nd:.2f}\nStd Below: {std_below_2nd:.2f}",
        transform=plt.gca().transAxes, fontsize=12, ha='right', va='top',
        bbox=dict(boxstyle="round,pad=0.3", edgecolor="black", facecolor="white"))
        plt.text(0.95, 0.35, f"Survival probability (atoms that remained): {survival:.2f}",
        transform=plt.gca().transAxes, fontsize=12, ha='right', va='top',
        bbox=dict(boxstyle="round,pad=0.3", edgecolor="black", facecolor="white"))
        plt.text(0.95, 0.25, f"False appearances (new atoms): {(false_appearance/total_positions):.2f}",
        transform=plt.gca().transAxes, fontsize=12, ha='right', va='top',
        bbox=dict(boxstyle="round,pad=0.3", edgecolor="black", facecolor="white"))

        
        plt.xlabel('photons')
        plt.ylabel('occurencies')
        plt.show()

        #one histogram for each tweezer second shot

        fig, ((ax1, ax2, ax3, ax4, ax5, ax6, ax7, ax8, ax9)) = plt.subplots(9, 1, figsize=(16, 26))

        axes = [ax1, ax2, ax3, ax4, ax5, ax6, ax7, ax8, ax9]
        photon_keys = ['11', '12', '13', '14', '15', '16', '17', '18', '19']
        titles = [f"ROI {i+1} (2nd shot)" for i in range(9)]

        for i, (ax, key, title) in enumerate(zip(axes, photon_keys, titles)):
        # for ax, key, title in zip(axes, photon_keys, titles):
            counts, bins, _ = ax.hist([photo_background_2nd, photons[key]], bins=binsG, color=['b', 'r'])

            if saving_data:
                bin_centers = (bins[:-1] + bins[1:]) / 2
                with open(histogram_data_csv, 'a', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    for b, c in zip(bin_centers, counts[0]):
                        writer.writerow([f"ROI {i+1} - Second Shot", b, c, 'BG'])
                    for b, c in zip(bin_centers, counts[1]):
                        writer.writerow([f"ROI {i+1} - Second Shot", b, c, 'Atoms'])


            ax.axvline(x=threshold, color='red', linestyle='--')
            ax.axvline(x=two_ph_threshold, color='red', linestyle='--')

            total_photons = len(photons[key])
            above_threshold = np.sum((np.array(photons[key]) > threshold) & (np.array(photons[key]) < two_ph_threshold))
            fraction = above_threshold / total_photons if total_photons > 0 else 0

            ax.text(0.95, 0.95, f"Above Threshold: {fraction:.2%}", 
                    transform=ax.transAxes, fontsize=12, ha='right', va='top',
                    bbox=dict(boxstyle="round,pad=0.3", edgecolor="black", facecolor="white"))
            ax.text(-0.1, 0.5, title, 
                    transform=ax.transAxes, fontsize=14, ha='right', va='center')

            ax.tick_params(axis='both', which='major', labelsize=12)
            ax.tick_params(axis='both', which='minor', labelsize=10)
            if i < len(axes) - 1:
                ax.tick_params(axis='x', which='both',
                       bottom=False, top=False,
                       labelbottom=False, labelleft=False) # Rimuove l'etichetta dell'asse x (se presente)  
            axes[-1].set_xlabel("Photon Counts", fontsize=14)
        # plt.tight_layout()
        plt.subplots_adjust(hspace=0.15)
        plt.show()


        #End of second shot analysis
        
        
    bimodalfit=1
        # threshold = 18 # Example threshold, replace with your actual value

    if bimodalfit:
        
        # Define the Gaussian function
        def gaussian(x, A, mu, sigma):
            return A * np.exp(-((x - mu)**2) / (2 * sigma**2))
        # Define the bimodal function (sum of two Gaussians)

        def bimodal(x, A1, mu1, sigma1, A2, mu2, sigma2):
            return gaussian(x, A1, mu1, sigma1) + gaussian(x, A2, mu2, sigma2)
        
        def gaussian_integral(A, mu, sigma, a, b):
            """Compute the integral of a Gaussian between limits a and b."""
            if a == -np.inf:
                erf_a = -1
            else:
                erf_a = erf((a - mu) / (sigma * np.sqrt(2)))

            if b == np.inf:
                erf_b = 1
            else:
                erf_b = erf((b - mu) / (sigma * np.sqrt(2)))

            return A * sigma * np.sqrt(2 * np.pi) * 0.5 * (erf_b - erf_a)
        
        # Example histogram data (replace with your data)
        hist, bin_edges = np.histogram(array_photons, bins=50, density=True)
        
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        
        # Initial guesses for A1, mu1, sigma1, A2, mu2, sigma2
        p0 = [0.1, 0, 5, 0.2, 50, 10]
        
        # Fit the bimodal model
        popt, pcov = curve_fit(bimodal, bin_centers, hist, p0=p0, maxfev=10000)
        print('ciao')
        # Extract parameters
        A1, mu1, sigma1, A2, mu2, sigma2 = popt

        # Threshold value
            
        # Integral of the left peak above the threshold
        left_above_threshold = gaussian_integral(A1, mu1, sigma1, threshold, np.inf)

        # Integral of the right peak below the threshold
        right_below_threshold = gaussian_integral(A2, mu2, sigma2, -np.inf, threshold)

        # Combined error measure
        separation_error = left_above_threshold + right_below_threshold

        print(f"Integral of left peak above threshold: {left_above_threshold:.4f}")
        print(f"Integral of right peak below threshold: {right_below_threshold:.4f}")
        print(f"Fidelity: {100-100*separation_error:.4f} %")
            
        plt.figure()
        # Plot the histogram and the fit
        plt.hist(array_photons, bins=50, density=True, alpha=0.6, color='g', label='Histogram')
        x = np.linspace(min(array_photons), max(array_photons), 1000)
        plt.plot(x, bimodal(x, *popt), 'r-', label='Bimodal fit')
        plt.plot(x, gaussian(x, A1, mu1, sigma1), 'b--', label='Gaussian 1')
        plt.plot(x, gaussian(x, A2, mu2, sigma2), 'y--', label='Gaussian 2')
        plt.axvline(threshold)
        plt.legend()
        plt.xlabel(f'Counts, Fidelity={100-100*separation_error:.2f} %')
        plt.ylabel(f'Density,{separation_error:.2f}')
        title=str(one_level_up+'\n first shot')
        plt.title(title,fontsize=14)
        plt.show()

        FluoAnalyser.save("threshold",)



except:
    pass

