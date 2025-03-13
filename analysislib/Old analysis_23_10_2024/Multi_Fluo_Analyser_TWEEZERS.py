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

def data_mean(para, values):
    para=parameter
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
    if len(aa)>=2:error=eN
    return x, y, error

def save_imag(plt, name):
    picname = name
    img_name=str(dt) + '_' + str(datetime.datetime.now().hour) + str(datetime.datetime.now().minute) + str(datetime.datetime.now().second)  + '_' + parameter_name
    plt.savefig(two_levels_up+ '/' + img_name +  '_' + picname + ".png")
    print(picname + ' saved')

def Tweezers_scan(value, title):
    figure()  ##################################################################### 
    for jj in range(n_tweezer):
        means_ii=tuple(value.get(str(jj+1)))
        x,y,error=data_mean(parameter, means_ii)
        plt.errorbar(x, y, yerr=error, fmt='--o', ecolor='gray',capsize=5)
    plt.legend(['1','2','3'])
    plt.xlabel(str(parameter_name)+' ('+str(scan_unit)+')')
    plt.title(title)
    plt.xlabel(str(parameter_name)+' ('+str(scan_unit)+')')
    plt.ylabel('photons')
    # plt.ylim(0,1)
    if saving_plots: save_imag(plt, title)  #####################################################################

###################################
saving_plots=True
n_tweezer=3
###################################

try: #iniziliation
    # Let's obtain the dataframe for all of lyse's currently loaded shots:
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

    print('optimization parameter =', parameter_name)

    parameter=np.array(df[parameter_name])

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
    Tweezers_scan(atoms, 'Occupation 0-1 in the tweezers')
    Tweezers_scan(photons, 'Photo-Count of Fluo Signal')

    figure()
    title='Histogram of Tweezer'
    plt.title(title)        
    data_background=photo_background
    # plt.ylim(0,1000)
    plt.hist([data_background,photons['1'],photons['2'], photons['3']] , bins=round(len(data_background)/5), color=['b','r','yellow','orange'  ]) #  
    plt.legend(['background', 'tweezer1','tweezer2','tweezer3'])
    plt.xlabel('photons')
    plt.ylabel('occurencies')
    plt.yscale('log')
    # plt.xlim(0,100)

    plt.show()
    save_imag(plt, title) 
except:
    pass

