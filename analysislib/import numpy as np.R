import numpy as np
import matplotlib.pyplot as plt

# Generate x values
x = np.linspace(-5, 5, 500)

# Gaussian function
mu = 0      # mean
sigma = 1   # standard deviation
y = np.exp(- (x - mu)**2 / (2 * sigma**2))

# Create plot
plt.figure()
plt.plot(x, y)
plt.title("Gaussian Curve")
plt.xlabel("x")
plt.ylabel("Amplitude")

# Save as SVG
plt.savefig("gaussian.svg", format="svg")

plt.close()