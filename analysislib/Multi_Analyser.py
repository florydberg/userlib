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

def save_imag(plt, name):
    picname = name
    img_name=str(dt) + '_' + str(datetime.datetime.now().hour) + str(datetime.datetime.now().minute) + str(datetime.datetime.now().second)  + '_' + parameter_name
    plt.savefig(two_levels_up+ '/' + img_name +  '_' + picname + ".png")
    print(picname + ' saved')

# Let's obtain the dataframe for all of lyse's currently loaded shots:
df = data()
paths=df['filepath']

AbAnalyser= df['AbsorbAnalyser']
# AbAnalyser= df['AbsorbAnalyser_Red']
number_of_atoms=tuple(AbAnalyser['number_of_atoms'])
sum_of_atoms=tuple(AbAnalyser['sum_of_atoms'])
peak_density=tuple(AbAnalyser['peak_density'])
waistawg=tuple(AbAnalyser['waistavg'])
waistx=tuple(AbAnalyser['waistx'])
waisty=tuple(AbAnalyser['waisty'])
centerx=tuple(AbAnalyser['centerx'])
centery=tuple(AbAnalyser['centery'])

parameter_name =AbAnalyser['scan_parameter'].iloc[-1]
scan_unit=AbAnalyser['scan_unit'].iloc[-1]

print('optimization parameter =', parameter_name)

parameter=np.array(df[parameter_name])
# parameter=np.multiply(parameter,1/1000)
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

if True:
    figure()
    x, y, stdev, std_error =data_mean(parameter, peak_density)
    xs, ys, stdevs, std_errors =data_mean(parameter, sum_of_atoms)

    # plt.ylabel()
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

    title='Peak density'
    plt.title(title)
    plt.xlabel(str(parameter_name)+' ('+str(scan_unit)+')')
    # plt.xlabel(str(parameter_name)+' ('+str(scan_unit)+')'+'\n'+ f"Fitted parameters: peak = {round((a_fit+offset)/1e6,2)} M, x_0 = {round(x0_fit,2)}, sigma_x = {round(sigma_fit,2)}")
    # plt.errorbar(x, y, stdev, fmt='-bo', ecolor='gray',capsize=5)
    plt.errorbar(x, y, yerr=std_error, fmt='--ro', ecolor='k',capsize=5)
    # plt.plot(x_data, gaussian(x_data, *params), color='red', label='Gaussian fit')
    # plt.errorbar(xs, ys, std_errors, fmt='-co', ecolor='c',capsize=5)
    # plt.legend(['Fitted','Raw'])
    # plt.legend(['Fitted'])
    save_imag(plt, title)

    figure()
    x, y, stdev, std_error =data_mean(parameter, number_of_atoms)
    xs, ys, stdevs, std_errors =data_mean(parameter, sum_of_atoms)
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

    title='Number Of Atoms'
    plt.title(title)
    plt.xlabel(str(parameter_name)+' ('+str(scan_unit)+')')
    # plt.xlabel(str(parameter_name)+' ('+str(scan_unit)+')'+'\n'+ f"Fitted parameters: peak = {round((a_fit+offset)/1e6,2)} M, x_0 = {round(x0_fit,2)}, sigma_x = {round(sigma_fit,2)}")
    # plt.errorbar(x, y, stdev, fmt='-bo', ecolor='gray',capsize=5)
    plt.errorbar(x, y, yerr=std_error, fmt='--bo', ecolor='k',capsize=5)
    # plt.plot(x_data, gaussian(x_data, *params), color='red', label='Gaussian fit')
    # plt.errorbar(xs, ys, std_errors, fmt='-co', ecolor='c',capsize=5)
    # plt.legend(['Fitted','Raw'])
    # plt.legend(['Fitted'])
    save_imag(plt, title)




    # figure()
    xw, yw, stdevw, std_errorw =data_mean(parameter, np.multiply(waistx,1000))

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
    print(f"Fitted parameters: Temp = {Temp_fit}, waist_i={waist_i}")

    # plt.ylabel('Waist X (mm)')
    # plt.xlabel(str(parameter_name)+' ('+str(scan_unit)+')')
    # plt.xlabel(str(parameter_name)+' (ms)')
    # plt.errorbar(xw, yw, yerr=std_errorw, fmt='--ro', ecolor='k',capsize=5)




    # figure()

    xw, yw, stdevw, std_errorw =data_mean(parameter, np.multiply(waisty,1000))

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
    print(f"Fitted parameters: Temp = {Temp_fit}, waist_i={waist_i}")


    # plt.ylabel('Waist Y (mm)')
    # plt.xlabel(str(parameter_name)+' ('+str(scan_unit)+')')
    # plt.xlabel(str(parameter_name)+' (ms)')
    # plt.errorbar(xw, yw, yerr=std_errorw, fmt='--bo', ecolor='k',capsize=5)
    # plt.plot(xw, plot_parabbola(xw, Temp_fit, waist_i), fmt='--ko', capsize=5)


    #Test to fit the average waist and plot the fit parameters
    figure()
    xw, yw, stdevw, std_errorw =data_mean(parameter, np.multiply(waistawg,1000))

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

    title='Waist avg (mm)'
    plt.title(title)
    plt.xlabel(str(parameter_name)+' ('+str(scan_unit)+'), Temperature = '+ str(round(Temp_fit*1e6, 2)) +' uK')
    plt.errorbar(xw, yw, yerr=std_errorw, fmt='--ro', ecolor='k',capsize=5)
    plt.plot(xw, plot_parabbola(xw, Temp_fit, waist_i),'-b')
    save_imag(plt, title)


        # writer.writerow([optimum,str(best_value), df['sequence'].iloc[-1], str(df['labscript'].iloc[-1])])

    if False: #switch to automatic updating of optimization parameter
        runmanager.remote.set_globals({opt_parameter: optimum})
        print('optimum set to global')


