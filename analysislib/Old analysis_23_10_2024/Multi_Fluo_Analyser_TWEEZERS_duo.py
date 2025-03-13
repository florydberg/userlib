from lyse import *
from pylab import *
import csv
import runmanager
from runmanager.remote import *
import numpy as np
import math
from scipy.optimize import curve_fit, least_squares
import numpy as np
import matplotlib.pyplot as plt
import datetime, time
import seaborn as sns
import pandas as pd
ts=time.time()
dt=datetime.datetime.now().date()

def saturation(dBm):
        Imag_beam_Power=400e-6/28*dBm #W   #TODO: update this value with the measure we have to take

        waist_0=6.667e-3 #m
        I=2*Imag_beam_Power/(np.pi*waist_0**2)
        lambda_laser = 461*1e-9
        delta=0
        Gam=32e6

        h=6.626e-34 #JHz^-1
        c=2.99e8 # m/s

        I_sat = (np.pi* h*c*Gam)/(3*lambda_laser**3) # previous calculation was 67.6
        sat=I*10000//I_sat/10000
        # sat=I/I_sat
        return sat

def data_mean(para, values):
    para=parameter1
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
    error = [std1[key] for key in x]
    eN= [stdN[key] for key in x]
    if len(aa)>=10:error=eN
    return x, y, error

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
        
        # Step 3: Compute mean, std, and error
        mean_values[pair] = np.mean(aa)
        std_values[pair] = np.std(aa)
        error_values[pair] = np.std(aa) / sqrt(len(aa))

        # Adjusting the error calculation if there are 10 or more values
        if len(aa) >= 10:
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
    sns.heatmap(df_pivot, annot=True, cmap="YlGnBu", linewidths=.5)
    
    # Add labels and a title
    plt.title("Heatmap of Mean Values across param1 and param2")
    plt.xlabel("param2")
    plt.ylabel("param1")
    
    plt.show()

def save_imag(plt, name):
    picname = name
    img_name=str(dt) + '_' + str(datetime.datetime.now().hour) + str(datetime.datetime.now().minute) + str(datetime.datetime.now().second)  + '_' + parameter_name
    plt.savefig(two_levels_up+ '/' + img_name +  '_' + picname + ".png")
    print(picname + ' saved')

def Tweezers_scan_duo(values, title):
    for jj in range(n_tweezer):
        figure()  ##################################################################### 
        values=tuple(values.get(str(jj+1)))
        mean_values, std_values, error_values = duo_mean(parameter2, parameter1, values)
        plot_heatmap(mean_values)

    plt.ylabel(str(para2_name)+ ' ('+str(para2_unit)+')')
    plt.xlabel(str(para1_name)+ ' ('+str(para1_unit)+')')
    plt.title(title)

    if saving_plots: save_imag(plt, title)  #####################################################################

###################################
saving_plots=True
tweezDim=7  
n_tweezer=1
para1_name='ImagingFluo_Pow'
para1_unit='dBm'
para2_name='FluoImgPulse_duration'
para2_unit='ms'
###################################
try: #iniziliation
    df = data()
    paths=df['filepath']
    FluoAnalyser= df['FluoAnalyser_TWEEZERS']

    means={}
    maxs={}
    vars={}
    photons={}
    atoms={}

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

    photo_background=tuple(FluoAnalyser['photo_background'])


    parameter_name =FluoAnalyser['scan_parameter'].iloc[-1]
    scan_unit=FluoAnalyser['scan_unit'].iloc[-1]



    parameter1=np.array(df[para1_name])
    parameter2=np.array(df[para2_name])

    if True:#conversion dbm to saturation parameter:
        parameter1=saturation(parameter1)
        para1_name='Saturation_Parameter'
        para1_unit='s'

    if True: #print list of shots in the characterization
        list_name=str(dt)  + '_' + str(datetime.datetime.now().hour)+ str(datetime.datetime.now().minute) +  str(datetime.datetime.now().second)  + '_' + parameter_name
        list_path=paths[-1]
        one_level_up = os.path.dirname(list_path)
        two_levels_up = os.path.dirname(one_level_up)
        # print(two_levels_up)

        file_name=list_name+'.csv'

        with open(two_levels_up+ '/' + file_name, 'a', newline='') as csv_file:
            writer = csv.writer(csv_file)
            for ii in paths:
                # print(ii)
                writer.writerow([ii])

    ###################################
    Tweezers_scan_duo(photons,'Fluorescence of Atoms')


except:
    pass





