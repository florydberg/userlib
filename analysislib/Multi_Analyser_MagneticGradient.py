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


# Define the Gaussian function
def gaussian(x, a, x0, sigma, offset):
    return offset+a * np.exp(-(x - x0)**2 / (2 * sigma**2))

def data_mean(para, values):
    data1 = {}
    std1 = {}
    stdN = {}
    for ii in set(para):

        indices = [idx for idx, val in enumerate(para) if val == ii]
        aa = [values[idx] for idx in indices]
        # aa = [values[idx] for idx in indices if values[idx] > 0]

        data1[ii] = np.mean(aa)
        std1[ii] = np.std(aa)
        stdN[ii] = np.std(aa)/sqrt(len(aa))
    x = sorted(data1.keys())
    y = [data1[key] for key in x]
    e = [std1[key] for key in x]
    eN= [stdN[key] for key in x]
    return x, y, e, eN

def data_organizing(para, para1, value1, value2):
    data1 = {}
    data2 = {}
    

    # Find indices where para1 matches the given parameter (para)
    indices = [idx for idx, param in enumerate(para1) if param == para]
    
    # Extract corresponding values from value1 and value2
    aa = [value1[idx] for idx in indices]
    bb = [value2[idx] for idx in indices]
    
    # Store these values in data1 and data2
    data1 = np.array(aa)
    data2 = np.array(bb)
    
    return data1, data2

# Let's obtain the dataframe for all of lyse's currently loaded shots:
df = data()
paths=df['filepath']

AbAnalyser= df['AbsorbAnalyser']


centerx=tuple(AbAnalyser['centerx'])
centery=tuple(AbAnalyser['centery'])

parameter1_name =AbAnalyser['scan_parameter'].iloc[-1]
parameter2_name = 'coils_current_cntrl'

scan_unit=AbAnalyser['scan_unit'].iloc[-1]

print('optimization parameter =', parameter1_name)
parameter1=np.array(df[parameter1_name])
parameter2=np.array(df[parameter2_name])



###############################################################################################
plt.figure(figsize=(10, 6))

colors = plt.cm.jet(np.linspace(0, 1, len(set(parameter1))))

list=parameter1

for i, para in enumerate(set(np.sort(list)[::-1])):
    span_I, Center = data_organizing(para, parameter1, parameter2, centerx)
    xx, yx, stdevx, std_errorx = data_mean(span_I, Center)
    plt.errorbar(xx, yx, yerr=std_errorx, fmt='-o', ecolor='gray', capsize=5, label=f'{round(para, 2)}V', color=colors[i])


# Add legend, labels, and title
plt.legend(loc='upper left')
plt.title('X0/B gradient at '+ str(parameter1_name))  # Replace with your plot title
plt.ylabel('Position of the X-center (um)')
plt.xlabel(str(parameter2_name)+' ('+str(scan_unit)+')')
# plt.ylim((1000,6000))
plt.show()

plt.figure(figsize=(10, 6))

colors = plt.cm.jet(np.linspace(0, 1, len(set(parameter1))))

list=parameter1

for i, para in enumerate(set(np.sort(list)[::-1])):
    span_I, Center = data_organizing(para, parameter1, parameter2, centery)
    xy, yy, stdevy, std_errory =data_mean(span_I, Center)
    plt.errorbar(xy, yy, yerr=std_errory, fmt='-o', ecolor='gray', capsize=5, label=f'{round(para, 2)}V', color=colors[i])

# Add legend, labels, and title
plt.legend(loc='upper left')
plt.title('Y0/B gradient at '+ str(parameter1_name))  # Replace with your plot title
plt.ylabel('Position of the Y-center (um)')
plt.xlabel(str(parameter2_name)+' ('+str(scan_unit)+')')
# plt.ylim((1000,6000))

plt.show()




#To save this result to the output hdf5 file, we have to instantiate a
#Sequence object:
for i in paths:
    seq = Sequence(i, df)
    # seq.save_results('optimum',optimum, 'number_of_atoms', best_value)

main_path=r'F:\Calibrations'

file_name=str(parameter1_name)+'.csv'
calibration_file=str(main_path+'\\'+file_name)
control=0
if not os.path.exists(calibration_file):
    control=1

with open(calibration_file, 'a', newline='') as csv_file:
    writer = csv.writer(csv_file)
    if control:
        writer.writerow([str(parameter_name), 'NumberOfAtoms', 'RunTime', 'Routine'])

    # writer.writerow([optimum,str(best_value), df['sequence'].iloc[-1], str(df['labscript'].iloc[-1])])

if False: #switch to automatic updating of optimization parameter
    runmanager.remote.set_globals({opt_parameter: optimum})
    print('optimum set to global')
