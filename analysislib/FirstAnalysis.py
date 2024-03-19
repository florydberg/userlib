from lyse import *
from pylab import *
from runmanager import *
import matplotlib.pyplot as plt
from scipy.optimize import fmin


data = data()
print(path)

# some_optimisation_process = MyOptimiser(initial_params)

# parameters = initial_params
# while True:
#     runmanager_remote.set_globals(parameters)
#     runmanager_remote.engage()
#     error_or_fitness = wait_for_lyse_routine_to_tell_me_the_result()
#     parameters = some_optimisation_process.do_one_iteration(error_or_fitness)



param_names = ['detuning', 'pulse_time']
initial_guess = [1e6, 10e-6]

def errorfunc(*params):
    runmanager_remote.set_globals({name: value for name, value in zip(param_names, params)})
    runmanager_remote.engage()
    error = wait_for_lyse_routine_to_tell_me_the_result()

best_params = fmin(errorfunc, initial_guess)