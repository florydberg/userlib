import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Dati
x = np.array([1, 2, 3, 4, 5])
y = np.array([11, 4.4, 0.93, -1.55, -3.47])

# Modello: funzione razionale con offset
def model(x, a1, a2, x0):
    return a1 / (x + x0) + a2

# Guess iniziale
p0 = [1.0, 0.0, 0.0]

# Fit
params, cov = curve_fit(model, x, y, p0=p0, maxfev=10000)
a1, a2, x0 = params

# Curve liscia
x_fit = np.linspace(min(x), max(x), 400)
y_fit = model(x_fit, a1, a2, x0)

# Plot
plt.figure()
plt.scatter(x, y, label="Dati")
plt.plot(
    x_fit,
    y_fit,
    label=f"Fit: y = {a1:.3f}/(x + {x0:.3f}) + {a2:.3f}"
)

plt.xlabel("N of Frequencies")
plt.ylabel("dBm")
plt.grid()
plt.legend()
plt.title("Fit con funzione 1/(x - x0) + offset")
plt.show()

print(f"a1 = {a1}")
print(f"a2 = {a2}")
print(f"x0 = {x0}")