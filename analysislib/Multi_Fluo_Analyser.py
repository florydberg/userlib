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
import matplotlib.ticker as ticker
ts=time.time()
dt=datetime.datetime.now().date()

# Define the Gaussian function
def gaussian(x, a, x0, sigma, offset):
    return offset + a * np.exp(-(x - x0)**2 / (2 * sigma**2))

# Define the Gaussian function
def parabbola(x, T, offset):
    mass = 1.67*88e-27
    kB=1.38*1e-23
    a=np.sqrt( offset**2+(kB*T/mass)*x*x)
    return a

def plot_parabbola(x, T, offset):
    mass = 1.67*88e-27
    kB=1.38*1e-23
    a=np.sqrt(offset**2+ kB*T/mass*np.square(x))
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

from collections import defaultdict
import numpy as np
from math import sqrt


def duo_mean(
    param1,
    param2,
    values,
    *,
    param1_mapping,
    param2_mapping
):
    """
    Compute mean, std and stderr per (param1_bin, param2_bin).

    param*_mapping MUST return an INTEGER bin index.
    """

    if not (len(param1) == len(param2) == len(values)):
        raise ValueError("param1, param2 and values must have the same length")

    bins = defaultdict(list)

    for p1, p2, v in zip(param1, param2, values):
        b1 = param1_mapping(p1)
        b2 = param2_mapping(p2)

        if b1 is None or b2 is None:
            continue

        bins[(b1, b2)].append(v)

    mean_values = {}
    std_values = {}
    error_values = {}

    for key, vals in bins.items():
        vals = np.asarray(vals)
        mean_values[key] = vals.mean()
        std_values[key] = vals.std()
        error_values[key] = vals.std() / sqrt(len(vals))

    return mean_values, std_values, error_values

def plot_heatmap(mean_values, param1_scan, param2_scan, title=""):
    """
    Plot heatmap from bin-indexed mean_values.
    """

    # Build DataFrame safely (NO duplicates possible)
    df = (
        pd.Series(mean_values, name="Mean")
        .unstack()
        .sort_index(axis=0)
        .sort_index(axis=1)
    )

    # Replace indices with physical scan values
    df.index = param1_scan[df.index]
    df.columns = param2_scan[df.columns]

    # Plot
    plt.figure(figsize=(8, 5))
    plt.rcParams.update({'font.size': 20})

    sns.heatmap( df, cmap="viridis", linewidths=0.5)

    plt.xlabel(para2_name + ' (' + para2_unit + ')')
    plt.ylabel(para1_name + ' (' + para1_unit + ')')
    plt.title(title)
    # plt.set_yticks(plt.get_yticks())
    # plt.set_yticklabels([f"{y:.2f}" for y in plt.get_yticks()])
    plt.tight_layout()
    plt.show()

def duo_scan(
    values,
    parameter1,
    parameter2,
    param1_scan,
    param2_scan,
    title=""
):
    """
    Full analysis pipeline:
    - bin
    - average
    - plot heatmap
    """

    # Integer-bin mappings (rock-solid)
    def param1_mapping(p):
        return int(np.argmin(np.abs(param1_scan - p)))

    def param2_mapping(p):
        return int(np.argmin(np.abs(param2_scan - p)))

    mean_values, std_values, error_values = duo_mean(
        parameter1,
        parameter2,
        values,
        param1_mapping=param1_mapping,
        param2_mapping=param2_mapping
    )

    plot_heatmap(
        mean_values,
        param1_scan=param1_scan,
        param2_scan=param2_scan,
        title=title
    )

    return mean_values, std_values, error_values

def mean_scan_duo(values, title):
    param1_scan = np.linspace(72.6,72.8,21) # in kHz
    param2_scan = np.linspace(22,30,9)
    # param2_scan = np.linspace(26,30,5)
    # param1_scan = np.linspace(0,360,10)
    # param2_scan = parameter2
    # param1_scan = parameter1



    duo_scan(
        values=values,
        parameter1=parameter1,
        parameter2=parameter2,
        param1_scan=param1_scan,
        param2_scan=param2_scan,
        title=title
    )
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
fit_TOF_waist = True
n_order=1000 # order of digits in parameter values
saving_data=True
fit_gaussian1= False

para1_name='coils_current_ctrl_red' #'n_shot'
para1_unit= 'V'    #'s' 
if duo:
    para2_name='Red_MOT_Pow_fin'
    para2_unit='dbm'

###################################################################################
try: #initialization

    # Let's obtain the dataframe for all of lyse's currently loaded shots:
    df = data()
    paths=df['filepath']
    runs = paths.str.extract(r'_(\d{4})_')[0].astype(int)
    unique_runs = sorted(runs.unique())
    run_str = "_".join(f"{r:04d}" for r in unique_runs)
    print(run_str)

    FluoAnalyser= df['FluoAnalyser']
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
        print('optimization parameter 2 =', parameter2)
        # print('optimization parameter 2 =', parameter2)
    #parameter_name = AbAnalyser['scan_parameter'].iloc[-1]
    #scan_unit=AbAnalyser['scan_unit'].iloc[-1]

    # number_of_atoms=tuple(AbAnalyser['number_of_atoms'])
    # sum_of_atoms=tuple(AbAnalyser['sum_of_atoms'])
    # peak_density=tuple(AbAnalyser['peak_density'])
    # waistavg=tuple(AbAnalyser['waistavg'])
    # waistx=tuple(AbAnalyser['waistx'])
    # waisty=tuple(AbAnalyser['waisty'])
    centerz=tuple(FluoAnalyser['centerx'])
    centery=tuple(FluoAnalyser['centery'])

    # parameter=np.array(df[parameter_name])
    # parameter=np.multiply(parameter,1/1000)

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

        # with open(two_levels_up+ '/' + file_name, 'a', newline='') as csv_file:
        #     writer = csv.writer(csv_file)
        #     for ii in paths:
        #         # print(ii)
        #         writer.writerow([ii])
        

    """ list_name=str(dt)  + '_' + str(datetime.datetime.now().hour)+ str(datetime.datetime.now().minute) +  str(datetime.datetime.now().second)  + '_' + parameter_name
    list_path=paths[-1]
    one_level_up = os.path.dirname(list_path)
    two_levels_up = os.path.dirname(one_level_up)
    print(two_levels_up)
    
    file_name=list_name+'.csv'

    with open(two_levels_up+ '/' + file_name, 'a', newline='') as csv_file:
        writer = csv.writer(csv_file)
        for ii in paths:
            # print(ii)
            writer.writerow([ii]) """

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

        # #Peak density plot
        # plt.figure(figsize=(5, 4))

        # x, y, stdev, std_error = data_mean(parameter1, peak_density)
        # peakks=y
        # std_peakks=std_error
        # xs, ys, stdevs, std_errors = data_mean(parameter1, sum_of_atoms)

        # title='Peak density'
        # plt.title(title,fontsize=25)
        # plt.xlabel(str(parameter_name)+' ('+str(para1_unit)+')',fontsize=30)
        # plt.ylabel(title,fontsize=30)
        # plt.errorbar(x, y, yerr=std_error, fmt='-o',
        #     markerfacecolor='lightgray', markeredgecolor='black', markersize=4,
        #     ecolor='black', capsize=3,label= 'data')
        
        # if fit_gaussian1:
        #     # Make an initial guess for the parameters [amplitude, mean, standard deviation]
        #     initial_guess = [max(y), mean(x), abs(max(x)-min(x))/8, 0*2e6]
        #     low = [0, 0, abs(max(x)-min(x))/32, 0*1e6]
        #     upper = [2*max(y), max(x), abs(max(x)-min(x)), 0.1*2.5e6]
        #     upper = [2*max(y), max(x), abs(max(x)-min(x)), 0.1*2.5e6]
        #     bounds = [low, upper]
        #     try:
        #         # Fit the data using curve_fit
        #         params, covariance = curve_fit(gaussian, x, y, p0=initial_guess, bounds=bounds )
        #         # Extract the fitted parameters
        #         a_fit, x0_fit, sigma_fit, offset = params
        #         # Print the fitted parameters
        #         print(f"Fitted parameters: amplitude = {a_fit}, mean = {x0_fit}, sigma = {sigma_fit}")
        #         plt.plot(x, gaussian(x, *params), color='blue', label='Gaussian fit')
        #         plt.text(0.02, 0.75, f"Fitted parameters:\n"
        #                 f"amplitude = {a_fit:.2e}\n"
        #                 f"mean = {x0_fit:.4e}\n"
        #                 f"sigma = {sigma_fit:.2e}\n"
        #                 f"offset = {offset:.2e}\n"
        #                 , transform=plt.gca().transAxes, fontsize=12, bbox=dict(facecolor='white', alpha=0.7))
        #         plt.legend()
        #     except Exception as e:
        #         print("An error occurred during curve fitting:", e)

        # if saving_data:
            
        #     print('Peak density data saved to data_peakDensity.csv')
        #     print("CSV saved in:", os.getcwd())
        #     # print (x, y, std_error)
        #     with open(two_levels_up + '/'+f"{dt}_{run_str}_"+'data_peakDensity.csv', 'w', newline='') as csv_file:
        #         print(csv_file)
        #         writer = csv.writer(csv_file)

        #         for ii in zip(x, y,  std_error, peakks, std_peakks):
        #             writer.writerow(ii)

        #         # print("Value",x)
        #         # print("Density", y)
        #         # print("err",std_error)
        #         # print("peak", peakks)
        #         # print("err_p",std_peakks)

        # save_imag(plt, title)

        # #Number of atoms plot
        # plt.figure(figsize=(3, 2))

        # x, y, stdev, std_error =data_mean(parameter1, number_of_atoms)
        # xs, ys, stdevs, std_errors =data_mean(parameter1, sum_of_atoms)
        # #plt.xlabel(str(parameter_name)+' ('+str(para1_unit)+')')

        # title='Number Of Atoms'
        # plt.title(title,fontsize=15)
        # plt.xlabel(str(parameter_name)+' ('+str(para1_unit)+')',fontsize=15)
        # # plt.ylabel(title,fontsize=15)
        # plt.errorbar(x, y, yerr=std_error, fmt='o', linestyle='-', color='black',
        #             markerfacecolor='lightgray', markeredgecolor='black', markersize=8,
        #             ecolor='black', capsize=4, label='data')

        # plt.ticklabel_format(style='sci', axis='y', scilimits=(0,0))

        # if fit_gaussian1:

        #     # Make an initial guess for the parameters [amplitude, mean, standard deviation]
        #     initial_guess = [max(y), mean(x), abs(max(x)-min(x))/8, 0*2e6]
        #     low = [0, 0, abs(max(x)-min(x))/32, 0*1e6]
        #     upper = [2*max(y), max(x), abs(max(x)-min(x)), 0.1*2.5e6]
        #     bounds = [low, upper]

        #     try:
        #         # Fit the data using curve_fit
        #         params, covariance = curve_fit(gaussian, x, y, p0=initial_guess, bounds=bounds )
        #         # Extract the fitted parameters
        #         a_fit, x0_fit, sigma_fit, offset = params
        #         # Print the fitted parameters
        #         print(f"Fitted parameters: amplitude = {a_fit}, mean = {x0_fit}, sigma = {sigma_fit}")
        #         plt.plot(x, gaussian(x, *params), color='b', label='Gaussian fit')
        #         plt.text(0.02, 0.75, f"Fitted parameters:\n"
        #             f"amplitude = {a_fit:.2e}\n"
        #             f"mean = {x0_fit:.4e}\n"
        #             f"sigma = {sigma_fit:.2e}\n"
        #             f"offset = {offset:.2e}\n"
        #             , transform=plt.gca().transAxes, fontsize=12, bbox=dict(facecolor='white', alpha=0.7))
        #         plt.legend()
        #     except Exception as e:
        #         print("An error occurred during curve fitting:", e)

        # if saving_data:
        #     print('Number of atoms data saved to data_numberOfAtom.csv')
        #     # print (x, y, std_error)
        #     with open(two_levels_up + '/'+f"{dt}_{run_str}_"+'data_numberOfAtom.csv', 'w', newline='') as csv_file:
        #         print(csv_file)
        #         writer = csv.writer(csv_file)

        #         for ii in zip(x, y,  std_error, peakks, std_peakks):
        #             writer.writerow(ii)

        #         # print("Value",x)
        #         # print("N", y)
        #         # print("err",std_error)
        #         # print("peak", peakks)
        #         # print("err_p",std_peakks)

        # save_imag(plt, title)

        # # Waist avg plot

        # if fit_TOF_waist:
        #     xw, yw, stdevw, std_errorw = data_mean(parameter1, np.multiply(waistavg,1000))
        #     # Make an initial guess for the parameters [amplitude, mean, standard deviation]
        #     initial_guess = [15e-6, 0.1]
        #     low = [0, 0]
        #     upper = [25e-3, 0.6]
        #     # upper = [25e-5, 0.3]
        #     bounds = [low, upper]

        #     # Fit the data using curve_fit
        #     params, covariance = curve_fit(parabbola, xw, yw, p0=initial_guess, bounds=bounds )

        #     # Extract the fitted parameters
        #     Temp_fit, waist_i = params

        #     # Print the fitted parameters
        #     # print(f"Fitted parameters: Temp = {Temp_fit}, waist_i={waist_i}")
        #     #figure()
        #     # plt.ylabel('Waist X (mm)')
        #     # plt.xlabel(str(parameter_name)+' ('+str(para1_unit)+')')
        #     # plt.xlabel(str(parameter_name)+' (ms)')
        #     # plt.errorbar(xw, yw, yerr=std_errorw, fmt='--ro', ecolor='k',capsize=5)

        #     # xw, yw, stdevw, std_errorw =data_mean(parameter1, np.multiply(waisty,1000))

        #     # initial_guess = [25e-6, 0.2]
        #     # low = [0, 0]
        #     # upper = [25e-3, 0.6]
        #     # # upper = [25e-5, 0.3]
        #     # bounds = [low, upper]

        #     # Fit the data using curve_fit
        #     # params, covariance = curve_fit(parabbola,xw, yw,p0=initial_guess, bounds=bounds )

        #     # Extract the fitted parameters
        #     Temp_fit, waist_i = params
        #     print(f"Fitted parameters: Temp = {Temp_fit}, waist_i={waist_i}")

        #     # Print the fitted parameters
        #     # print(f"Fitted parameters: Temp = {Temp_fit}, waist_i={waist_i}")
        #     #figure()
        #     # plt.ylabel('Waist Y (mm)')
        #     # plt.xlabel(str(parameter_name)+' ('+str(para1_unit)+')')
        #     # plt.xlabel(str(parameter_name)+' (ms)')
        #     # plt.errorbar(xw, yw, yerr=std_errorw, fmt='--bo', ecolor='k',capsize=5)
        #     # plt.plot(xw, plot_parabbola(xw, Temp_fit, waist_i), fmt='--ko', capsize=5)

        # xw, yw, stdevw, std_errorw =data_mean(parameter1, np.multiply(waistavg,1000))
        # print( xw)
        # print( yw)
        # print( std_errorw)
        # print( stdevw)
        
        # #Test to fit the average waist and plot the fit parameters
        # # Make an initial guess for the parameters [amplitude, mean, standard deviation]
        # initial_guess = [35e-6, 0.36]
        # low = [1e-6, 0.00]
        # upper = [45e-2, 0.7]
        # bounds = [low, upper]
        # # Fit the data using curve_fit
        # params, covariance = curve_fit(parabbola, xw, yw, p0=initial_guess, bounds=bounds)
        
        # # Extract the fitted parameters
        # Temp_fit, waist_i = params
        # # Print the fitted parameters
        # print(f"Fitted parameters: Temp = {Temp_fit}, waist_i={waist_i}")

        # figure()
        # plt.rcParams.update({'font.size': 22})

        # # plt.errorbar(xw, yw, yerr=std_errorw, fmt='--ro', ecolor='k',capsize=5)
        # plt.errorbar(xw, yw, yerr=std_errorw, fmt='o',linestyle='None',
        #     markerfacecolor='lightgray', markeredgecolor='black', markersize=4,
        #     ecolor='black', capsize=3,)
        
        # plt.title('Waist avg',fontsize=25)

        # plt.ylabel('Waist avg (mm)',fontsize=25)
        # if fit_TOF_waist:
        #     if True:
        #         plt.plot(xw, plot_parabbola(xw, Temp_fit, waist_i), linestyle='-', color='black', label='Parabola fit')
        #     plt.xlabel(str(parameter_name)+' ('+str(para1_unit)+'), Temperature = '+ str(round(Temp_fit*1e6, 2)) +' uK', fontsize=25)
        # else:
        #     plt.xlabel(str(parameter_name)+' ('+str(para1_unit)+')')
        # plt.legend(['Raw','Fitted'])
        
        # title = 'Waist avg'

        # if saving_plots: save_imag(plt, title)

        # writer.writerow([optimum,str(best_value), df['sequence'].iloc[-1], str(df['labscript'].iloc[-1])])

        # xs, ys, stdevs, std_errors = data_mean(parameter1, sum_of_atoms)

        # # plt.ylabel()
        
        # plt.xlabel(str(parameter_name)+' ('+str(para1_unit)+')')

        # if saving_data:
        #     print('waist avg data saved to waist_avg.csv')
        #     with open(two_levels_up + '/'+f"{dt}_{run_str}_"+'waist_avg.csv', 'w', newline='') as csv_file:
        #         print(csv_file)
        #         writer = csv.writer(csv_file)

        # # Make an initial guess for the parameters [amplitude, mean, standard deviation]
        # initial_guess = [max(y), mean(x), 2, 2e6]
        # low = [0, 0, 0, 1e6]
        # upper = [2*max(y), max(x), 5, 2.5e6]
        # bounds = [low, upper]

        # Fit the data using curve_fit
        # params, covariance = curve_fit(gaussian, x, y, p0=initial_guess, bounds=bounds )

        # Extract the fitted parameters
        # a_fit, x0_fit, sigma_fit, offset = params

        # Print the fitted parameters
        # print(f"Fitted parameters: amplitude = {a_fit}, mean = {x0_fit}, sigma = {sigma_fit}")

        title='Center along z'
        figure()
        x, y, stdev, std_error = data_mean(parameter1, centerz)
        plt.title(title,fontsize=25)
        plt.xlabel(str(parameter_name)+' ('+str(para1_unit)+')')
        # plt.xlabel(str(parameter_name)+' ('+str(para1_unit)+')'+'\n'+ f"Fitted parameters: peak = {round((a_fit+offset)/1e6,2)} M, x_0 = {round(x0_fit,2)}, sigma_x = {round(sigma_fit,2)}")
        # plt.errorbar(x, y, stdev, fmt='-bo', ecolor='gray',capsize=5)
        plt.errorbar(x, y, yerr=std_error, fmt='--go', ecolor='k',capsize=5)
        # plt.plot(x, gaussian(x, *params), color='red', label='Gaussian fit')
        # plt.errorbar(xs, ys, std_errors, fmt='-co', ecolor='c',capsize=5)
        # plt.legend(['Fitted','Raw'])
        # plt.legend(['Fitted'])
        save_imag(plt, title)

        
        figure()
        x, y, stdev, std_error = data_mean(parameter1, centery)
        # plt.ylabel()
        plt.xlabel(str(parameter_name)+' ('+str(para1_unit)+')')


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


