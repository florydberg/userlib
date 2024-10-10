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

def Tweezers_scan(means, vars):
    

    figure()  ##################################################################### 
    for ii in range(n_tweezer):

        means_ii=tuple(means.get(str(ii+1)))
        print(means_ii)
        print(type(means_ii))

        para=parameter
        values=means_ii
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
        std_error = [std1[key] for key in x]
        eN= [stdN[key] for key in x]

        plt.xlabel(str(parameter_name)+' ('+str(scan_unit)+')')

        title='Mean of Fluo Signal'
        plt.title(title)
        plt.xlabel(str(parameter_name)+' ('+str(scan_unit)+')')
        plt.errorbar(x, y, yerr=std_error, fmt='--o', ecolor='k',capsize=5)
        plt.legend(['1','2','3'])
        save_imag(plt, title)   #####################################################################


    
    figure()  #####################################################################
    for ii in range(n_tweezer):
        vars_ii=tuple(vars.get(str(ii+1)))
        print(vars_ii)
        
        # xs, ys, std_errors =data_mean(parameter, vars_ii)
        para=parameter
        values=vars_ii
        data1 = {}
        std1 = {}
        stdN = {}
        for ii in set(para):
            indices = [idx for idx, val in enumerate(para) if val == ii]
            aa = [values[idx] for idx in indices]
            data1[ii] = np.mean(aa)
            std1[ii] = np.std(aa)
            stdN[ii] = np.std(aa)/sqrt(len(aa))
        xs = sorted(data1.keys())
        ys = [data1[key] for key in x]
        std_error = [std1[key] for key in x]
        eN= [stdN[key] for key in x]


        plt.xlabel(str(parameter_name)+' ('+str(scan_unit)+')')

        title='Variance of Fluo Signal'
        plt.title(title)
        plt.xlabel(str(parameter_name)+' ('+str(scan_unit)+')')
        plt.errorbar(xs, ys, yerr=std_error, fmt='--o', ecolor='k',capsize=5)
        plt.legend(['1','2','3'])
        save_imag(plt, title)  #####################################################################

# Let's obtain the dataframe for all of lyse's currently loaded shots:
df = data()
paths=df['filepath']

FluoAnalyser= df['FluoAnalyser']

n_tweezer=3
means={}
vars={}
for ii in range(0,n_tweezer):
    mean_name='mean_tweezer_'+str(ii+1)
    means[str(ii+1)]=tuple(FluoAnalyser[mean_name])
    mm=tuple(FluoAnalyser[mean_name])
    var_name='variance_tweezer_'+str(ii+1)
    vars[str(ii+1)]=(tuple(FluoAnalyser[var_name]))
    vv=tuple(FluoAnalyser[var_name])


print(means)

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

Tweezers_scan(means, vars)
