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
dtf = datetime.datetime.now()

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

    df = (
        pd.Series(mean_values, name="Mean")
        .unstack()
        .sort_index(axis=0)
        .sort_index(axis=1)
    )

    df.index = param1_scan[df.index]
    df.columns = param2_scan[df.columns]

    plt.figure(figsize=(8, 5))
    plt.rcParams.update({'font.size': 20})

    ax = sns.heatmap(df, cmap="viridis", linewidths=0.5)

    plt.xlabel(para2_name + ' (' + para2_unit + ')')
    plt.ylabel(para1_name + ' (' + para1_unit + ')')
    plt.title(title + " - " + dataset_label )

    ax.set_xticklabels([f"{x:.2f}" for x in df.columns])
    ax.set_yticklabels([f"{y:.1f}" for y in df.index])

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
        title=title + " - " + dataset_label
    )

    return mean_values, std_values, error_values

def mean_scan_duo(values, title):

    # param1_scan = np.linspace(-3,3,31)
    # param2_scan = np.linspace(-3,3,31)
    # param2_scan = parameter2
    # param1_scan = parameter1



    duo_scan(
        values=values,
        parameter1=parameter1,
        parameter2=parameter2,
        param1_scan=param1_scan,
        param2_scan=param2_scan,
        title=title + " - " + dataset_label
    )
    print("Heatmap data saved to heatmap_data.csv")

    if saving_plots: save_imag(plt, title)  #####################################################################

def save_imag(plt, name):
    picname = name
    if duo:
        img_name = (f"{dt}_{run_str}_{para1_name}_{para2_name}")
    else:
        img_name = (f"{dt}_{run_str}_{para1_name}")
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

para1_name='FluoImgPulse_Dt' #'n_shot'
para1_unit= 'ms'    #'s' 
if duo:
    para2_name='LAC_duration'
    para2_unit='s'

param1_scan = np.linspace(-5,0,21) # in kHz
param2_scan = np.linspace(1,10,10)
###################################################################################
try: #initialization

    # Let's obtain the dataframe for all of lyse's currently loaded shots:
    df = data()
    paths=df['filepath']
    runs = paths.str.extract(r'_(\d{4})_')[0].astype(int)
    unique_runs = sorted(runs.unique())
    run_str = "_".join(f"{r:04d}" for r in unique_runs)
    print(run_str)
    if len(unique_runs) == 1:
        dataset_label = f"dataset {unique_runs[0]:04d}"
    else:
        dataset_label = f"dataset {unique_runs[0]:04d}-{unique_runs[-1]:04d}"

    FluoAnalyser= df['FluoAnalyser_tweez']
    # AbAnalyser= df['AbsorbAnalyser_old']
    means={}
    maxs={}
    vars={}
    photons={}
    atoms={}

    parameter1=np.array(df[para1_name])
    #print('optimization parameter 1 =', parameter1)
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

    for i in range(1, 37):
        globals()[f"itw{i}"] = tuple(FluoAnalyser[f"tw{i}_integral"])

    for i in range(1, 37):
        globals()[f"itw{i}_2nd"] = tuple(FluoAnalyser[f"tw{i}_integral_2nd"])


    itw = tuple(
    value
    for i in range(1, 37)
    for value in FluoAnalyser[f"tw{i}_integral"]
    )
    itw_2nd = tuple(
    value
    for i in range(1, 37)
    for value in FluoAnalyser[f"tw{i}_integral_2nd"]
    )


    # ihalo=tuple(FluoAnalyser['Halo_integral'])

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
        img_name= str(dt) + '_' + dtf.strftime("%H") + dtf.strftime("%M") + dtf.strftime("%S") + '_' +dtf.strftime("%f") + '_' + para1_name + '_' + para2_name
    if duo:
        print('duo analysis Tw3')
        value = tuple(elem_1 // elem_2 for elem_1, elem_2 in zip(itw, ihalo))

        mean_scan_duo(itw3,'Tweezer Sum integral')
        # mean_scan_duo(peak_density,'Peak density')
        df.to_csv(two_levels_up+ '/' + img_name + '_tw3' + '.csv', index=False)

        # print('duo analysis Halo')
        # mean_scan_duo(ihalo,'Halo  integral')
        # img_name+='_' + para1_name + '_' + para2_name + '_density'
        # df.to_csv(two_levels_up+ '/' + img_name + '_halo' + '.csv', index=False)      


    else:
        print('single analysis')

        # #plot the mean
        # ys = []
        # errors = []

        # for itw in [itw1, itw2, itw3, itw4, itw5, itw6, itw7, itw8, itw9]:
        #     x, y, stdev, std_error = data_mean(parameter1, itw)
        #     ys.append(y)
        #     errors.append(std_error)

        # ys = np.array(ys)
        # errors = np.array(errors)

        # # media delle 9 curve
        # y_mean = np.mean(ys, axis=0)

        # # deviazione standard tra le 9 curve
        # y_std = np.std(ys, axis=0, ddof=1)

        # # errore standard della media
        # y_sem = y_std / np.sqrt(ys.shape[0])

        # # figure(figsize=(10, 2))
        # title = 'Tweez ROI integral mean'

        # # plt.title(title, fontsize=25)
        # # plt.xlabel(f'{parameter_name} ({para1_unit})')

        # # plt.errorbar(
        # #     x,
        # #     y_mean,
        # #     yerr=y_sem,
        # #     fmt='--ko',
        # #     ecolor='k',
        # #     capsize=5
        # # )

        # # save_imag(plt, title)

        # fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)

        # # ---------- TOP: all individual tweezers ----------
        # ax = axes[0]
        # title = 'Tweez ROI integral '

        # ax.set_title(title+dataset_label, fontsize=20)
        # ax.set_xlabel(f'{parameter_name} ({para1_unit})')

        # colors = ['k', 'b', 'r', 'g', 'c', 'm', 'y', 'purple', 'brown']
        # itws = [itw1, itw2, itw3, itw4, itw5, itw6, itw7, itw8, itw9]

        # ys = []
        # errors = []

        # for itw, color in zip(itws, colors):
        #     x, y, stdev, std_error = data_mean(parameter1, itw)
            
        #     ax.errorbar(
        #         x, y,
        #         yerr=std_error,
        #         fmt='--o',
        #         color=color,
        #         ecolor=color,
        #         capsize=5
        #     )
            
        #     ys.append(y)
        #     errors.append(std_error)

        # # ---------- BOTTOM: mean ----------
        # ax2 = axes[1]
        # title_mean = 'Tweez ROI integral mean'

        # ys = np.array(ys)

        # y_mean = np.mean(ys, axis=0)
        # y_std = np.std(ys, axis=0, ddof=1)
        # y_sem = y_std / np.sqrt(ys.shape[0])

        # ax2.set_title(title_mean, fontsize=20)
        # ax2.set_xlabel(f'{parameter_name} ({para1_unit})')

        # ax2.errorbar(
        #     x,
        #     y_mean,
        #     yerr=y_sem,
        #     fmt='--ko',
        #     ecolor='k',
        #     capsize=5
        # )

        # # ---------- layout & save ----------
        # plt.tight_layout()
        # save_imag(plt, 'Tweez_ROI_combined')
        
        

        # ============================================================
        # FIRST SHOT
        # itw1 ... itw36
        # ============================================================

        itws_first = [
            globals()[f"itw{i}"]
            for i in range(1, 37)
        ]

        ys_first = []
        errors_first = []

        for itw in itws_first:
            x, y, stdev, std_error = data_mean(parameter1, itw)

            ys_first.append(y)
            errors_first.append(std_error)

        ys_first = np.array(ys_first)
        errors_first = np.array(errors_first)

        # Media delle 36 curve
        y_mean_first = np.mean(ys_first, axis=0)

        # Deviazione standard tra le 36 curve
        y_std_first = np.std(ys_first, axis=0, ddof=1)

        # Errore standard della media
        y_sem_first = y_std_first / np.sqrt(ys_first.shape[0])


        # ============================================================
        # SECOND SHOT
        # itw1_2nd ... itw36_2nd
        # ============================================================

        itws_second = [
            globals()[f"itw{i}_2nd"]
            for i in range(1, 37)
        ]

        ys_second = []
        errors_second = []

        for itw in itws_second:
            x, y, stdev, std_error = data_mean(parameter1, itw)

            ys_second.append(y)
            errors_second.append(std_error)

        ys_second = np.array(ys_second)
        errors_second = np.array(errors_second)

        # Media delle 36 curve
        y_mean_second = np.mean(ys_second, axis=0)

        # Deviazione standard tra le 36 curve
        y_std_second = np.std(ys_second, axis=0, ddof=1)

        # Errore standard della media
        y_sem_second = y_std_second / np.sqrt(ys_second.shape[0])


        # ============================================================
        # PLOT
        # ============================================================

        fig, axes = plt.subplots(
            2, 1,
            figsize=(10, 6),
            sharex=True
        )


        # ---------- TOP: First Shot ----------

        ax = axes[0]

        ax.set_title(
            'Tweez ROI integral mean (First Shot)' + dataset_label,
            fontsize=20
        )

        ax.set_ylabel('ROI integral')

        ax.errorbar(
            x,
            y_mean_first,
            yerr=y_sem_first,
            fmt='--ko',
            ecolor='k',
            capsize=5
        )


        # ---------- BOTTOM: Second Shot ----------

        ax2 = axes[1]

        ax2.set_title(
            'Tweez ROI integral mean (Second Shot)' + dataset_label,
            fontsize=20
        )

        ax2.set_xlabel(f'{parameter_name} ({para1_unit})')
        ax2.set_ylabel('ROI integral')

        ax2.errorbar(
            x,
            y_mean_second,
            yerr=y_sem_second,
            fmt='--ko',
            ecolor='k',
            capsize=5
        )


        # ---------- layout & save ----------

        plt.tight_layout()

        save_imag(
            plt,
            'Tweez_ROI_mean_First_Second_Shot'
        )



        # save_imag(plt, title)
        if False: #switch to automatic updating of optimization parameter
            runmanager.remote.set_globals({opt_parameter: optimum})
            print('optimum set to global')
except Exception as e:
    print("An error occurred during analysis:", e)


