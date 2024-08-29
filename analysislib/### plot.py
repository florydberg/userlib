### plot
from scipy.optimize import curve_fit, least_squares
import numpy as np
import matplotlib.pyplot as plt


fr=[77.9,77.67,77.02]
pow=[20,14,7]

plt.title('power Red Profile')
plt.xlabel("Blue-Power(mW)")


plt.plot(pow, frq, color='red', label='Gaussian fit')
# plt.errorbar(xs, ys, stdevs, fmt='-co', ecolor='c',capsize=5)
# plt.legend(['Fitted','Raw'])
plt.legend(['Fitted'])
