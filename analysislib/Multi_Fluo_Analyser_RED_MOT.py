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
import pandas as pd
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

def Red_Mot_scan(peaks, devs, centers):
    x, y, stdev, std_error =data_mean(parameter, peaks)
    print(centers)
    print(type(centers))


    figure()  #####################################################################
    plt.xlabel(str(parameter_name)+' ('+str(scan_unit)+')')

    x_data = x
    y_data = y

    title='Peaks of Red MOT'
    plt.title(title)
    plt.xlabel(str(parameter_name)+' ('+str(scan_unit)+')')
    plt.errorbar(x, y, yerr=std_error, fmt='--ro', ecolor='k',capsize=5)
    save_imag(plt, title)   #####################################################################

    figure()  #####################################################################
    plt.xlabel(str(parameter_name)+' ('+str(scan_unit)+')')

    xs, ys, stdevs, std_errors =data_mean(parameter, devs)

    title='Waist of Red MOT'
    plt.title(title)
    plt.xlabel(str(parameter_name)+' ('+str(scan_unit)+')')
    plt.errorbar(xs, ys, yerr=std_error, fmt='--bo', ecolor='k',capsize=5)
    save_imag(plt, title)  #####################################################################

    x_0=zeros(len(parameter))
    y_0=zeros(len(parameter))

    for ii in range(len(parameter)):
        x_0[ii],y_0[ii]=centers[ii]
    print(x_0)

    figure()  #####################################################################
    plt.xlabel(str(parameter_name)+' ('+str(scan_unit)+')')

    xx, yx, stdevx, std_errorx =data_mean(parameter, x_0)

    title='X0 of Red MOT'
    plt.title(title)
    plt.xlabel(str(parameter_name)+' ('+str(scan_unit)+')')
    plt.errorbar(xx, yx-ones(len(yx))*mean(yx), yerr=std_errorx, fmt='--ro', ecolor='k',capsize=5)
    plt.ylabel('um')
    save_imag(plt, title)  #####################################################################

    figure()  #####################################################################
    plt.xlabel(str(parameter_name)+' ('+str(scan_unit)+')')

    xy, yy, stdevy, std_errory =data_mean(parameter, y_0)

    title='Y0 of Red MOT'
    plt.title(title)
    plt.xlabel(str(parameter_name)+' ('+str(scan_unit)+')')
    plt.errorbar(xy, ones(len(yy))*mean(yy)-yy, yerr=std_errory, fmt='--bo', ecolor='k',capsize=5)
    plt.ylabel('um')
    save_imag(plt, title)  #####################################################################

# Let's obtain the dataframe for all of lyse's currently loaded shots:
df = data()
paths=df['filepath']

FluoAnalyser= df['FluoAnalyser_RED_MOT']
peaks=tuple(FluoAnalyser['peak_RedMot'])
waists=tuple(FluoAnalyser['waist_RedMot'])
centers=tuple(FluoAnalyser['center_RedMot'])


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

Red_Mot_scan(peaks, waists, centers)
