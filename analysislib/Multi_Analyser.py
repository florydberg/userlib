from lyse import *
from pylab import *
import csv
import runmanager
from runmanager.remote import *
import numpy as np

def data_mean(para, values):
    data1 = {}
    std1 = {}
    for ii in set(para):
        indices = [idx for idx, val in enumerate(para) if val == ii]
        aa = [values[idx] for idx in indices]
        data1[ii] = np.mean(aa)
        std1[ii] = np.std(aa)
    x = sorted(data1.keys())
    y = [data1[key] for key in x]
    e = [std1[key] for key in x]
    return x, y, e

# Let's obtain the dataframe for all of lyse's currently loaded shots:
df = data()
paths=df['filepath']

AbAnalyser= df['AbsorbAnalyser']
number_of_atoms=tuple(AbAnalyser['number_of_atoms'])
peak_density=tuple(AbAnalyser['peak_density'])
main_waist=tuple(AbAnalyser['main_waist'])

parameter_name =AbAnalyser['scan_parameter']

print('optimization parameter =', parameter_name)
parameter=np.array(df[parameter_name])

###############################################################################################
# Let's plot them against each other:

figure()
x, y, stdev =data_mean(parameter, peak_density)
plt.ylabel('Peak Density')

plt.title('Optimization Profile')
plt.xlabel(str(parameter_name))
plt.errorbar(x, y, stdev, fmt='-ro', ecolor='gray',capsize=5)


best_value=max(y)
optimum=x[y.index(max(y))]
optimum=optimum

figure()
x, y, stdev =data_mean(parameter, number_of_atoms)
plt.ylabel('Number Of Atoms')

plt.title('Optimization Profile')
plt.xlabel(str(parameter_name))
plt.errorbar(x, y, stdev, fmt='-bo', ecolor='gray',capsize=5)

figure()
x, y, stdev =data_mean(parameter, main_waist)
plt.ylabel('Main Waist')

plt.title('Optimization Profile')
plt.xlabel(str(parameter_name))
plt.errorbar(x, y, stdev, fmt='-ko', ecolor='gray',capsize=5)


##################################################################################
print('\n-----------------------------------\n')
print('best value is ', optimum, 'for', parameter_name)
print('\n-----------------------------------')

#To save this result to the output hdf5 file, we have to instantiate a
#Sequence object:
for i in paths:
    seq = Sequence(i, df)
    seq.save_results('optimum',optimum, 'number_of_atoms', best_value)

main_path=r'F:\Calibrations'

file_name=str(parameter_name)+'.csv'
calibration_file=str(main_path+'\\'+file_name)
control=0
if not os.path.exists(calibration_file):
    control=1

with open(calibration_file, 'a', newline='') as csv_file:
    writer = csv.writer(csv_file)
    if control:
        writer.writerow([str(parameter_name), 'NumberOfAtoms', 'RunTime', 'Routine'])

    writer.writerow([optimum,str(best_value), df['sequence'].iloc[-1], str(df['labscript'].iloc[-1])])

if False: #switch to automatic updating of optimization parameter
    runmanager.remote.set_globals({opt_parameter: optimum})
    print('optimum set to global')
