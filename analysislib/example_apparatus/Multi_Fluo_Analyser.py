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
ts=time.time()
dt=datetime.datetime.now().date()

# Define the Gaussian function
def gaussian(x, a, x0, sigma, offset):
    return offset+a * np.exp(-(x - x0)**2 / (2 * sigma**2))

# Define the Gaussian function
def parabbola(x, T, offset):
    mass = 1.67*88e-27
    kB=1.38*1e-23
    a=sqrt(offset**2+ kB*T/mass*x*x)
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

def save_imag(plt, name):
    picname = name
    img_name=str(dt) + '_' + str(datetime.datetime.now().hour) + str(datetime.datetime.now().minute) + str(datetime.datetime.now().second)  + '_' + parameter_name
    plt.savefig(two_levels_up+ '/' + img_name +  '_' + picname + ".png")
    print(picname + ' saved')

def Tweezers_scan(peaks, devs):
    x, y, stdev, std_error =data_mean(parameter, peaks)
    print(peaks)
    print(type(peaks))
    xs, ys, stdevs, std_errors =data_mean(parameter, devs)

    figure()  #####################################################################
    plt.xlabel(str(parameter_name)+' ('+str(scan_unit)+')')

    x_data = x
    y_data = y
    # Make an initial guess for the parameters [amplitude, mean, standard deviation]
    initial_guess = [max(y), mean(x), 2, 2e6]
    low = [0, 0, 0, 1e6]
    upper = [2*max(y), max(x), 5, 2.5e6]
    bounds = [low, upper]

    # Fit the data using curve_fit
    # params, covariance = curve_fit(gaussian, x_data, y_data, p0=initial_guess, bounds=bounds )

    # Extract the fitted parameters
    # a_fit, x0_fit, sigma_fit, offset = params

    # Print the fitted parameters
    # print(f"Fitted parameters: amplitude = {a_fit}, mean = {x0_fit}, sigma = {sigma_fit}")

    title='Peaks of Fluo Signal'
    plt.title(title)
    plt.xlabel(str(parameter_name)+' ('+str(scan_unit)+')')
    # plt.xlabel(str(parameter_name)+' ('+str(scan_unit)+')'+'\n'+ f"Fitted parameters: peak = {round((a_fit+offset)/1e6,2)} M, x_0 = {round(x0_fit,2)}, sigma_x = {round(sigma_fit,2)}")
    # plt.errorbar(x, y, stdev, fmt='-bo', ecolor='gray',capsize=5)
    plt.errorbar(x, y, yerr=std_error, fmt='--ro', ecolor='k',capsize=5)
    # plt.plot(x_data, gaussian(x_data, *params), color='red', label='Gaussian fit')
    # plt.errorbar(xs, ys, std_errors, fmt='-co', ecolor='c',capsize=5)
    # plt.legend(['Fitted','Raw'])
    # plt.legend(['Fitted'])
    save_imag(plt, title)   #####################################################################

    figure()  #####################################################################
    plt.xlabel(str(parameter_name)+' ('+str(scan_unit)+')')


    x_data = x
    y_data = y


    # Make an initial guess for the parameters [amplitude, mean, standard deviation]
    initial_guess = [max(y), mean(x), 2, 2e6]
    low = [0, 0, 0, 1e6]
    upper = [2*max(y), max(x), 5, 2.5e6]
    bounds = [low, upper]

    # Fit the data using curve_fit
    # params, covariance = curve_fit(gaussian, x_data, y_data, p0=initial_guess, bounds=bounds )

    # Extract the fitted parameters
    # a_fit, x0_fit, sigma_fit, offset = params

    # Print the fitted parameters
    # print(f"Fitted parameters: amplitude = {a_fit}, mean = {x0_fit}, sigma = {sigma_fit}")

    title='Standard Deviations of Fluo Signal'
    plt.title(title)
    plt.xlabel(str(parameter_name)+' ('+str(scan_unit)+')')
    # plt.xlabel(str(parameter_name)+' ('+str(scan_unit)+')'+'\n'+ f"Fitted parameters: peak = {round((a_fit+offset)/1e6,2)} M, x_0 = {round(x0_fit,2)}, sigma_x = {round(sigma_fit,2)}")
    # plt.errorbar(x, y, stdev, fmt='-bo', ecolor='gray',capsize=5)
    plt.errorbar(xs, ys, yerr=std_error, fmt='--bo', ecolor='k',capsize=5)
    # plt.plot(x_data, gaussian(x_data, *params), color='red', label='Gaussian fit')
    # plt.errorbar(xs, ys, std_errors, fmt='-co', ecolor='c',capsize=5)
    # plt.legend(['Fitted','Raw'])
    # plt.legend(['Fitted'])
    save_imag(plt, title)  #####################################################################

# Let's obtain the dataframe for all of lyse's currently loaded shots:
df = data()
paths=df['filepath']

FluoAnalyser= df['FluoAnalyser']
# AbAnalyser= df['AbsorbAnalyser_Red']
peaks1=tuple(FluoAnalyser['peak_tweezer_1'])
devs1=tuple(FluoAnalyser['deviation_tweezer_1'])
peaks2=tuple(FluoAnalyser['peak_tweezer_2'])
devs2=tuple(FluoAnalyser['deviation_tweezer_2'])
peaks3=tuple(FluoAnalyser['peak_tweezer_3'])
devs3=tuple(FluoAnalyser['deviation_tweezer_3'])


parameter_name =FluoAnalyser['scan_parameter'].iloc[-1]
scan_unit=FluoAnalyser['scan_unit'].iloc[-1]

print('optimization parameter =', parameter_name)

parameter=np.array(df[parameter_name])

if True: #print list of shots in the characterization
    list_name=str(dt)  + '_' + str(datetime.datetime.now().hour)+ str(datetime.datetime.now().minute) +  str(datetime.datetime.now().second)  + '_' + parameter_name
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

###############################################################################################

Tweezers_scan(peaks2, devs2)
