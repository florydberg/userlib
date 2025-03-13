from lyse import *
from pylab import *
import csv
import runmanager
from runmanager.remote import *

def take_second(elem):
    return elem[1]

# Let's obtain the dataframe for all of lyse's currently loaded shots:
df = data()
paths=df['filepath']

AbAnalyser= df['AbsorbAnalyser']
number_of_atoms=AbAnalyser['number_of_atoms']
peak_density=AbAnalyser['peak_density']
main_waist=AbAnalyser['main_waist']

opt_parameter = 'Imaging_Frq'

print('optimization parameter =', opt_parameter)
parameter=df[opt_parameter]

###############################################################################################

opt_data1=[parameter.array, peak_density.array]
print(opt_data1)



# Let's plot them against each other:
plt.title('Optimization Profile')
plt.xlabel(str(opt_parameter))
plt.ylabel('Peak Density')
plot(opt_data1[0], opt_data1[1],'ro',label='optimization profile')

best_value=max(number_of_atoms)
optimum=parameter[number_of_atoms==best_value].iloc[0]
# optimum=optimum.iloc[0]

# figure()
# plt.title('Optimization Profile')
# plt.xlabel(str(opt_parameter))
# plt.ylabel('Number of Atoms')
# plot(parameter, peak_density,'-ro')

# figure()
# plt.title('Optimization Profile')
# plt.xlabel(str(opt_parameter))
# plt.ylabel('Main Waist')
# plot(parameter, peak_density,'-b')

##################################################################################
print('\n-----------------------------------\n')
print('best value is ', optimum, 'for', opt_parameter)
print('\n-----------------------------------')

#To save this result to the output hdf5 file, we have to instantiate a
#Sequence object:
for i in paths:
    seq = Sequence(i, df)
    seq.save_results('optimum',optimum, 'number_of_atoms', best_value)

main_path=r'F:\Calibrations'

file_name=str(opt_parameter)+'.csv'
calibration_file=str(main_path+'\\'+file_name)
control=0
if not os.path.exists(calibration_file):
    control=1

with open(calibration_file, 'a', newline='') as csv_file:
    writer = csv.writer(csv_file)
    if control:
        writer.writerow([str(opt_parameter), 'NumberOfAtoms', 'RunTime', 'Routine'])

    writer.writerow([optimum,str(round(best_value/1000))+'e3', df['sequence'].iloc[-1], str(df['labscript'].iloc[-1])])

if False: #switch to automatic updating of optimization parameter
    runmanager.remote.set_globals({opt_parameter: optimum})
    print('optimum set to global')
