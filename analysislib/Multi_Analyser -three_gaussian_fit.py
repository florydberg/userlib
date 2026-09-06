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
dtf = datetime.datetime.now()

# Define the Gaussian function
def gaussian(x, a, x0, sigma, offset):
    return offset + a * np.exp(-(x - x0)**2 / (2 * sigma**2))

# Define the Gaussian function
def gaussian3(x, A0, x0, s0, A1, dx1, s1, A2, dx2, s2, offset):
    """
    dx1, dx2 = distanza delle gaussiane laterali dal centro centrale x0
    """
    return (
        A0 * np.exp(-(x - x0)**2 / (2 * s0**2)) +
        A1 * np.exp(-(x - (x0 - dx1))**2 / (2 * s1**2)) +
        A2 * np.exp(-(x - (x0 + dx2))**2 / (2 * s2**2)) +
        offset
    )

def parabbola(x, T, offset):
    mass = 1.67*88e-27
    kB=1.38*1e-23
    a=sqrt( offset**2+kB*T/mass*x*x)
    return a

def plot_parabbola(x, T, offset):
    mass = 1.67*88e-27
    kB=1.38*1e-23
    a=sqrt(offset**2+ kB*T/mass*np.square(x))
    return a

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
    param1=tuple(round(i*n_order)/n_order for i in param1)
    param2=tuple(round(i*n_order)/n_order for i in param2)
    
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
    
    # Adjust param2 values by subtracting the offset
    offset=20
    # Mapping for param1 (y-axis) 3d
    # param1_mapping = {
    #     23: 0.054,
    #     24: 0.064,
    #     25: 0.075,
    #     26: 0.086,
    #     27: 0.093,
    #     28: 0.097,
    #     29: 0.100,
    # }
    param1_mapping = {
        25: 64,
        26: 95,
        27: 144,
        28: 221,
        29: 309,
    }
    param2_mapping = {
        74.84: -180,
        74.85: -160,
        74.86: -140,
        74.87: -120,
        74.88: -100,
        74.89: -80,
        74.90: -60,
        74.91: -40,
        74.92: -20,
    }
    # param1_mapping = {
    #     23: 6.2e-2,
    #     24: 7.3e-2,
    #     25: 8.4e-2,
    #     26: 9.5e-2,
    #     27: 10.3e-2,
    #     28: 10.7e-2,
    #     29: 11.1e-2,
    # }
    df['adjusted_param2'] = df['param2'].map(param2_mapping)
    df['adjusted_param1'] = df['param1'].map(param1_mapping)
    # Step 2: Pivot the DataFrame to create a matrix format
    df_pivot = df.pivot(index='adjusted_param1', columns='adjusted_param2', values='Mean Value')
    # Step 2: Pivot the DataFrame to create a matrix format
    # df_pivot = df.pivot(index='param1', columns='param2', values='Mean Value')

    # Step 3: Plot the heatmap
    plt.figure(figsize=(8, 5))
    plt.rcParams.update({'font.size': 20})
    sns.heatmap(df_pivot, annot=False, fmt='.2e', cmap="viridis", linewidths=.5)
    
    # Add labels and a title
    plt.title("Heatmap of Mean Values across param1 and param2")
    # plt.xlabel("param2")
    plt.xlabel("2D MOT beams detuning (MHz)")
    plt.ylabel("param1")
    plt.show()

def mean_scan_duo(values, title):
    values=tuple(values)
    mean_values, std_values, error_values = duo_mean(parameter2, parameter1, values)
    plot_heatmap(mean_values)


    plt.ylabel(str(para2_name)+ ' ('+str(para2_unit)+')')
    xlabel=str(para1_name)+' ('+str(para1_unit)+')'
    if saving_location:
        xlabel+='\n' + 'dataset:'+ str(one_level_up)
    plt.xlabel(xlabel)
    plt.title(title)


    print("Heatmap data saved to heatmap_data.csv")

    if saving_plots: save_imag(plt, title)  #####################################################################

def save_imag(plt, name):
    picname = name
    if duo:
        img_name = (f"{dt}_{run_str}_{para1_name}_{para2_name}")
        # img_name=str(dt) + '_' + str(datetime.datetime.now().hour) + str(datetime.datetime.now().minute) + str(datetime.datetime.now().second)  + '_' + para1_name + '_' + para2_name
    else:
        img_name = (f"{dt}_{run_str}_{para1_name}")
        # img_name=str(dt)  + '_' + str(datetime.datetime.now().hour)+ str(datetime.datetime.now().minute) +  str(datetime.datetime.now().second)  + '_' + para1_name
    plt.savefig(two_levels_up+ '/' + img_name +  '_' + picname + ".png")
    print(picname + ' saved')


################################### 
duo=0
saving_plots=True
saving_location=True
fit_TOF_waist = False
n_order=1000 # order of digits in parameter values
saving_data=True
fit_gaussian1= False
fit_gaussian3=True

para1_name='Red_MOT_Frq' #'n_shot'
para1_unit= 'MHz'    #'s' 
if duo:
    para2_name='MOT_RED_duration'
    para2_unit='ms'

###################################################################################
try: #initialization
    # Let's obtain the dataframe for all of lyse's currently loaded shots:
    df = data()
    paths=df['filepath']
    runs = paths.str.extract(r'_(\d{4})_')[0].astype(int)
    unique_runs = sorted(runs.unique())
    run_str = "_".join(f"{r:04d}" for r in unique_runs)
    print(run_str)

    AbAnalyser= df['AbsorbAnalyser']
    # AbAnalyser= df['AbsorbAnalyser_old']
    means={}
    maxs={}
    vars={}
    photons={}
    atoms={}

    parameter1=np.array(df[para1_name])
    # print('optimization parameter 1 =', parameter1)
    parameter_name = para1_name
    if duo:
        parameter2=np.array(df[para2_name])
        # print('optimization parameter 2 =', parameter2)
    #parameter_name = AbAnalyser['scan_parameter'].iloc[-1]
    #scan_unit=AbAnalyser['scan_unit'].iloc[-1]

    number_of_atoms=tuple(AbAnalyser['number_of_atoms'])
    sum_of_atoms=tuple(AbAnalyser['sum_of_atoms'])
    peak_density=tuple(AbAnalyser['peak_density'])
    waistawg=tuple(AbAnalyser['waistavg'])
    waistx=tuple(AbAnalyser['waistx'])
    waisty=tuple(AbAnalyser['waisty'])
    centerx=tuple(AbAnalyser['centerx'])
    centery=tuple(AbAnalyser['centery'])

    # parameter=np.array(df[parameter_name])
    # parameter=np.multiply(parameter,1/1000)

    if True: #print list of shots in the characterization
        list_name = str(dt) + '_' + dtf.strftime("%H") + dtf.strftime("%M") + dtf.strftime("%S") + '_' +dtf.strftime("%f") + '_' + para1_name
        if duo:
            list_name += '_' + para2_name
        list_path=paths[-1]
        one_level_up = os.path.dirname(list_path)
        two_levels_up = os.path.dirname(one_level_up)
        print(two_levels_up)
        file_name=list_name+'.csv'


    ###############################################################################################

    if duo:
        print('duo analysis')
        mean_scan_duo(number_of_atoms,'Number of atoms')
        # mean_scan_duo(peak_density,'Peak density')
        img_name=str(dt) + '_' + str(datetime.datetime.now().hour) + str(datetime.datetime.now().minute) + str(datetime.datetime.now().second)  
        img_name+='_' + para1_name + '_' + para2_name + '_density'
        df.to_csv(two_levels_up+ '/' + img_name + '.csv', index=False)

        print('duo analysis')
        mean_scan_duo(peak_density,'Peak density')
        img_name=str(dt) + '_' + str(datetime.datetime.now().hour) + str(datetime.datetime.now().minute) + str(datetime.datetime.now().second)  
        img_name+='_' + para1_name + '_' + para2_name + '_density'
        df.to_csv(two_levels_up+ '/' + img_name + '.csv', index=False)      


    else:
        print('single analysis')

        #Peak density plot
        plt.figure(figsize=(5, 4))

        x, y, stdev, std_error = data_mean(parameter1, peak_density)
        peakks=y
        std_peakks=std_error
        xs, ys, stdevs, std_errors = data_mean(parameter1, sum_of_atoms)

        title='Peak density'
        plt.title(title,fontsize=25)
        plt.xlabel(str(parameter_name)+' ('+str(para1_unit)+')',fontsize=30)
        plt.ylabel(title,fontsize=30)
        plt.errorbar(x, y, yerr=std_error, fmt='-o',
            markerfacecolor='lightgray', markeredgecolor='black', markersize=4,
            ecolor='black', capsize=3,label= 'data')
        
        if fit_gaussian1:
            # Make an initial guess for the parameters [amplitude, mean, standard deviation]
            initial_guess = [max(y), mean(x), abs(max(x)-min(x))/8, 0*2e6]
            low = [0, 0, abs(max(x)-min(x))/32, 0*1e6]
            upper = [2*max(y), max(x), abs(max(x)-min(x)), 0.1*2.5e6]
            upper = [2*max(y), max(x), abs(max(x)-min(x)), 0.1*2.5e6]
            bounds = [low, upper]
            try:
                # Fit the data using curve_fit
                params, covariance = curve_fit(gaussian, x, y, p0=initial_guess, bounds=bounds )
                # Extract the fitted parameters
                a_fit, x0_fit, sigma_fit, offset = params
                # Print the fitted parameters
                print(f"Fitted parameters: amplitude = {a_fit}, mean = {x0_fit}, sigma = {sigma_fit}")
                plt.plot(x, gaussian(x, *params), color='blue', label='Gaussian fit')
                plt.text(0.02, 0.75, f"Fitted parameters:\n"
                        f"amplitude = {a_fit:.2e}\n"
                        f"mean = {x0_fit:.4e}\n"
                        f"sigma = {sigma_fit:.2e}\n"
                        f"offset = {offset:.2e}\n"
                        , transform=plt.gca().transAxes, fontsize=12, bbox=dict(facecolor='white', alpha=0.7))
                plt.legend()
            except Exception as e:
                print("An error occurred during curve fitting:", e)

        if fit_gaussian3:
            # initial guess
            A0 = max(y)
            x0 = mean(x)
            s0 =5

            A1 = A0 * 0.8
            A2 = A0 * 0.8
            dx1 = 10
            dx2 = 10
            s1 = s0
            s2 = s0
            offset0 = min(y)

            initial_guess = [A0, x0, s0, A1, dx1, s1, A2, dx2, s2, offset0]

            low = [0, 70, 2, 0, 6, 2, 0, 6, 2, -np.inf]

            upper = [2*A0, max(x), abs(max(x)-min(x)), 2*A0, abs(max(x)-min(x)), abs(max(x)-min(x)), 2*A0, abs(max(x)-min(x)), abs(max(x)-min(x)), np.inf]

            bounds = [low, upper]

            try:
                params, covariance = curve_fit(gaussian3, x, y,p0=initial_guess,bounds=bounds)

                (A0, x0, s0, A1, dx1, s1, A2, dx2, s2, offset) = params

                print("=== 3-Gaussian fit ===")
                print(f"Central:   A={A0:.2e}, x0={x0:.4e}, sigma={s0:.2e}")
                print(f"Left:      A={A1:.2e}, dx={-dx1:.4e}, sigma={s1:.2e}")
                print(f"Right:     A={A2:.2e}, dx={dx2:.4e}, sigma={s2:.2e}")
                print(f"Offset:    {offset:.2e}")

                plt.plot(x, gaussian3(x, *params), color='blue', label='3-Gaussian fit')

                plt.text(
                    0.02, 0.65,
                    f"3-Gaussian fit\n"
                    f"x0 = {x0:.3e}\n"
                    f"dx L = {-dx1:.3e}\n"
                    f"dx R = {dx2:.3e}\n"
                    f"s0 = {s0:.2e}\n"
                    f"sL = {s1:.2e}\n"
                    f"sR = {s2:.2e}",
                    transform=plt.gca().transAxes,
                    fontsize=11,
                    bbox=dict(facecolor='white', alpha=0.7)
                )

                plt.legend()

            except Exception as e:
                print("An error occurred during 3-Gaussian fitting:", e)

        
        if saving_data:
            
            print('Peak density data saved to data_peakDensity.csv')
            print("CSV saved in:", os.getcwd())
            # print (x, y, std_error)
            with open(two_levels_up + '/'+f"{dt}_{run_str}_"+'data_peakDensity.csv', 'w', newline='') as csv_file:
                print(csv_file)
                writer = csv.writer(csv_file)

                for ii in zip(x, y,  std_error, peakks, std_peakks):
                    writer.writerow(ii)

                # print("Value",x)
                # print("Density", y)
                # print("err",std_error)
                # print("peak", peakks)
                # print("err_p",std_peakks)

        save_imag(plt, title)

        #Number of atoms plot
        plt.figure(figsize=(5, 4))

        x, y, stdev, std_error =data_mean(parameter1, number_of_atoms)
        xs, ys, stdevs, std_errors =data_mean(parameter1, sum_of_atoms)
        #plt.xlabel(str(parameter_name)+' ('+str(para1_unit)+')')

        title='Number Of Atoms'
        plt.title(title,fontsize=25)
        plt.xlabel(str(parameter_name)+' ('+str(para1_unit)+')',fontsize=30)
        plt.ylabel(title,fontsize=30)
        plt.errorbar(x, y, yerr=std_error, fmt='o',linestyle='-', color='black',
        markerfacecolor='lightgray', markeredgecolor='black', markersize=8,
        ecolor='black', capsize=4, label='data')

        if fit_gaussian1:

            # Make an initial guess for the parameters [amplitude, mean, standard deviation]
            initial_guess = [max(y), mean(x), abs(max(x)-min(x))/8, 0*2e6]
            low = [0, 0, abs(max(x)-min(x))/32, 0*1e6]
            upper = [2*max(y), max(x), abs(max(x)-min(x)), 0.1*2.5e6]
            bounds = [low, upper]

            try:
                # Fit the data using curve_fit
                params, covariance = curve_fit(gaussian, x, y, p0=initial_guess, bounds=bounds )
                # Extract the fitted parameters
                a_fit, x0_fit, sigma_fit, offset = params
                # Print the fitted parameters
                print(f"Fitted parameters: amplitude = {a_fit}, mean = {x0_fit}, sigma = {sigma_fit}")
                plt.plot(x, gaussian(x, *params), color='b', label='Gaussian fit')
                plt.text(0.02, 0.75, f"Fitted parameters:\n"
                    f"amplitude = {a_fit:.2e}\n"
                    f"mean = {x0_fit:.4e}\n"
                    f"sigma = {sigma_fit:.2e}\n"
                    f"offset = {offset:.2e}\n"
                    , transform=plt.gca().transAxes, fontsize=12, bbox=dict(facecolor='white', alpha=0.7))
                plt.legend()
            except Exception as e:
                print("An error occurred during curve fitting:", e)

        if fit_gaussian3:
            # initial guess
            A0 = max(y)
            x0 = mean(x)
            s0 = abs(max(x) - min(x)) / 10

            A1 = A0 / 2
            A2 = A0 / 2
            dx1 = abs(max(x) - min(x)) / 6
            dx2 = dx1
            s1 = s0
            s2 = s0
            offset0 = 0

            initial_guess = [A0, x0, s0, A1, dx1, s1, A2, dx2, s2, offset0]

            low = [0, min(x), 0, 0, 0, 0, 0, 0, 0, -np.inf]

            upper = [2*A0, max(x), abs(max(x)-min(x)), 2*A0, abs(max(x)-min(x)), abs(max(x)-min(x)), 2*A0, abs(max(x)-min(x)), abs(max(x)-min(x)), np.inf]

            bounds = [low, upper]

            try:
                params, covariance = curve_fit(gaussian3, x, y,p0=initial_guess,bounds=bounds)

                (A0, x0, s0, A1, dx1, s1, A2, dx2, s2, offset) = params

                print("=== 3-Gaussian fit ===")
                print(f"Central:   A={A0:.2e}, x0={x0:.4e}, sigma={s0:.2e}")
                print(f"Left:      A={A1:.2e}, dx={-dx1:.4e}, sigma={s1:.2e}")
                print(f"Right:     A={A2:.2e}, dx={dx2:.4e}, sigma={s2:.2e}")
                print(f"Offset:    {offset:.2e}")

                plt.plot(x, gaussian3(x, *params), color='blue', label='3-Gaussian fit')

                plt.text(
                    0.02, 0.65,
                    f"3-Gaussian fit\n"
                    f"x0 = {x0:.3e}\n"
                    f"dx L = {-dx1:.3e}\n"
                    f"dx R = {dx2:.3e}\n"
                    f"s0 = {s0:.2e}\n"
                    f"sL = {s1:.2e}\n"
                    f"sR = {s2:.2e}",
                    transform=plt.gca().transAxes,
                    fontsize=11,
                    bbox=dict(facecolor='white', alpha=0.7)
                )

                plt.legend()

            except Exception as e:
                print("An error occurred during 3-Gaussian fitting:", e)


        if saving_data:
            print('Number of atoms data saved to data_numberOfAtom.csv')
            # print (x, y, std_error)
            with open(two_levels_up + '/'+f"{dt}_{run_str}_"+'data_numberOfAtom.csv', 'w', newline='') as csv_file:
                print(csv_file)
                writer = csv.writer(csv_file)

                for ii in zip(x, y,  std_error, peakks, std_peakks):
                    writer.writerow(ii)

                # print("Value",x)
                # print("N", y)
                # print("err",std_error)
                # print("peak", peakks)
                # print("err_p",std_peakks)

        save_imag(plt, title)

        # Waist avg plot

        if fit_TOF_waist:
            xw, yw, stdevw, std_errorw =data_mean(parameter1, np.multiply(waistx,1000))
            # Make an initial guess for the parameters [amplitude, mean, standard deviation]
            initial_guess = [25e-6, 0.2]
            low = [0, 0]
            upper = [25e-3, 0.6]
            # upper = [25e-5, 0.3]
            bounds = [low, upper]

            # Fit the data using curve_fit
            params, covariance = curve_fit(parabbola, xw, yw, p0=initial_guess, bounds=bounds )

            # Extract the fitted parameters
            Temp_fit, waist_i = params

            # Print the fitted parameters
            # print(f"Fitted parameters: Temp = {Temp_fit}, waist_i={waist_i}")
            #figure()
            # plt.ylabel('Waist X (mm)')
            # plt.xlabel(str(parameter_name)+' ('+str(para1_unit)+')')
            # plt.xlabel(str(parameter_name)+' (ms)')
            # plt.errorbar(xw, yw, yerr=std_errorw, fmt='--ro', ecolor='k',capsize=5)

            xw, yw, stdevw, std_errorw =data_mean(parameter1, np.multiply(waisty,1000))

            initial_guess = [25e-6, 0.2]
            low = [0, 0]
            upper = [25e-3, 0.6]
            # upper = [25e-5, 0.3]
            bounds = [low, upper]

            # Fit the data using curve_fit
            # params, covariance = curve_fit(parabbola,xw, yw,p0=initial_guess, bounds=bounds )

            # Extract the fitted parameters
            Temp_fit, waist_i = params

            # Print the fitted parameters
            # print(f"Fitted parameters: Temp = {Temp_fit}, waist_i={waist_i}")
            #figure()
            # plt.ylabel('Waist Y (mm)')
            # plt.xlabel(str(parameter_name)+' ('+str(para1_unit)+')')
            # plt.xlabel(str(parameter_name)+' (ms)')
            # plt.errorbar(xw, yw, yerr=std_errorw, fmt='--bo', ecolor='k',capsize=5)
            # plt.plot(xw, plot_parabbola(xw, Temp_fit, waist_i), fmt='--ko', capsize=5)

        xw, yw, stdevw, std_errorw =data_mean(parameter1, np.multiply(waistawg,1000))
        #Test to fit the average waist and plot the fit parameters
        # Make an initial guess for the parameters [amplitude, mean, standard deviation]
        initial_guess = [35e-6, 0.36]
        low = [1e-6, 0.00]
        upper = [45e-2, 0.7]
        bounds = [low, upper]
        # Fit the data using curve_fit
        params, covariance = curve_fit(parabbola, xw, yw, p0=initial_guess, bounds=bounds)
        # Extract the fitted parameters
        Temp_fit, waist_i = params
        # Print the fitted parameters
        print(f"Fitted parameters: Temp = {Temp_fit}, waist_i={waist_i}")

        figure()
        plt.rcParams.update({'font.size': 22})

        # plt.errorbar(xw, yw, yerr=std_errorw, fmt='--ro', ecolor='k',capsize=5)
        plt.errorbar(xw, yw, yerr=std_errorw, fmt='o',linestyle='None',
            markerfacecolor='lightgray', markeredgecolor='black', markersize=4,
            ecolor='black', capsize=3,)
        
        plt.title('Waist avg',fontsize=25)

        plt.ylabel('Waist avg (um)',fontsize=25)
        if fit_TOF_waist:
            if True:
                plt.plot(xw, plot_parabbola(xw, Temp_fit, waist_i), linestyle='-', color='black', label='Parabola fit')
            plt.xlabel(str(parameter_name)+' ('+str(para1_unit)+'), Temperature = '+ str(round(Temp_fit*1e6, 2)) +' uK', fontsize=25)
        else:
            plt.xlabel(str(parameter_name)+' ('+str(para1_unit)+')')
        plt.legend(['Raw','Fitted'])
        
        title = 'Waist avg'

        if saving_plots: save_imag(plt, title)

        # writer.writerow([optimum,str(best_value), df['sequence'].iloc[-1], str(df['labscript'].iloc[-1])])
        figure()
        x, y, stdev, std_error = data_mean(parameter1, centery)
        xs, ys, stdevs, std_errors = data_mean(parameter1, sum_of_atoms)

        # plt.ylabel()
        
        plt.xlabel(str(parameter_name)+' ('+str(para1_unit)+')')

        # Make an initial guess for the parameters [amplitude, mean, standard deviation]
        initial_guess = [max(y), mean(x), 2, 2e6]
        low = [0, 0, 0, 1e6]
        upper = [2*max(y), max(x), 5, 2.5e6]
        bounds = [low, upper]

        # Fit the data using curve_fit
        # params, covariance = curve_fit(gaussian, x, y, p0=initial_guess, bounds=bounds )

        # Extract the fitted parameters
        # a_fit, x0_fit, sigma_fit, offset = params

        # Print the fitted parameters
        # print(f"Fitted parameters: amplitude = {a_fit}, mean = {x0_fit}, sigma = {sigma_fit}")

        title='Center along x'
        plt.title(title,fontsize=25)
        plt.xlabel(str(parameter_name)+' ('+str(para1_unit)+')')
        # plt.xlabel(str(parameter_name)+' ('+str(para1_unit)+')'+'\n'+ f"Fitted parameters: peak = {round((a_fit+offset)/1e6,2)} M, x_0 = {round(x0_fit,2)}, sigma_x = {round(sigma_fit,2)}")
        # plt.errorbar(x, y, stdev, fmt='-bo', ecolor='gray',capsize=5)
        plt.errorbar(x, y, yerr=std_error, fmt='--ro', ecolor='k',capsize=5)
        # plt.plot(x, gaussian(x, *params), color='red', label='Gaussian fit')
        # plt.errorbar(xs, ys, std_errors, fmt='-co', ecolor='c',capsize=5)
        # plt.legend(['Fitted','Raw'])
        # plt.legend(['Fitted'])
        save_imag(plt, title)
        figure()
        x, y, stdev, std_error = data_mean(parameter1, centery)
        xs, ys, stdevs, std_errors = data_mean(parameter1, sum_of_atoms)

        # plt.ylabel()
        plt.xlabel(str(parameter_name)+' ('+str(para1_unit)+')')

        # Make an initial guess for the parameters [amplitude, mean, standard deviation]
        initial_guess = [max(y), mean(x), 2, 2e6]
        low = [0, 0, 0, 1e6]
        upper = [2*max(y), max(x), 5, 2.5e6]
        bounds = [low, upper]

        # Fit the data using curve_fit
        # params, covariance = curve_fit(gaussian, x, y, p0=initial_guess, bounds=bounds )

        # Extract the fitted parameters
        # a_fit, x0_fit, sigma_fit, offset = params

        # Print the fitted parameters
        # print(f"Fitted parameters: amplitude = {a_fit}, mean = {x0_fit}, sigma = {sigma_fit}")

        title='Center along y'
        plt.title(title,fontsize=25)
        plt.xlabel(str(parameter_name)+' ('+str(para1_unit)+')')
        # plt.xlabel(str(parameter_name)+' ('+str(para1_unit)+')'+'\n'+ f"Fitted parameters: peak = {round((a_fit+offset)/1e6,2)} M, x_0 = {round(x0_fit,2)}, sigma_x = {round(sigma_fit,2)}")
        # plt.errorbar(x, y, stdev, fmt='-bo', ecolor='gray',capsize=5)
        plt.errorbar(x, y, yerr=std_error, fmt='--ro', ecolor='k',capsize=5)
        # plt.plot(x, gaussian(x, *params), color='red', label='Gaussian fit')
        # plt.errorbar(xs, ys, std_errors, fmt='-co', ecolor='c',capsize=5)
        # plt.legend(['Fitted','Raw'])
        # plt.legend(['Fitted'])
        save_imag(plt, title)
        if False: #switch to automatic updating of optimization parameter
            runmanager.remote.set_globals({opt_parameter: optimum})
            print('optimum set to global')
except Exception as e:
    print("An error occurred during analysis:", e)


