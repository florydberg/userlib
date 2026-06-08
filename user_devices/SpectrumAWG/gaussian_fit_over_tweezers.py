import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from tifffile import imread

# --- Load image
image_path = "5x5tweezers.tif"
img = imread(image_path).astype(float)

# --- Collapse image to get intensity profiles
x_profile = np.sum(img, axis=0)
if x_profile.ndim > 1:
    x_profile = np.sum(x_profile, axis=1)
x_profile=x_profile-np.min(x_profile)

y_profile = np.sum(img, axis=1)
if y_profile.ndim > 1:
    y_profile = np.sum(y_profile, axis=1)
y_profile=y_profile-np.min(y_profile)

x = np.arange(len(x_profile))
y = np.arange(len(y_profile))

# --- Define standard Gaussian
def gaussian(x, A, mu, sigma, offset):
    return A * np.exp(-(x - mu)**2 / (2 * sigma**2)) + offset

# --- Guess initial fit parameters
def guess_init(profile, axis):
    A = np.max(profile) - np.min(profile)
    mu = np.sum(axis * profile) / np.sum(profile)
    sigma = np.sqrt(np.sum(profile * (axis - mu)**2) / np.sum(profile))
    offset = np.min(profile)
    return A, mu, sigma, offset

init_x = guess_init(x_profile, x)
init_y = guess_init(y_profile, y)

# --- Fit
popt_x, _ = curve_fit(gaussian, x, x_profile, p0=init_x)
popt_y, _ = curve_fit(gaussian, y, y_profile, p0=init_y)

popt_x[0] =  np.max(x_profile)
popt_y[0] = np.max(y_profile)

popt_x[2] *= 2
popt_y[2] *= 2

# --- Normalize fitted Gaussian to match max of profile
gauss_x = gaussian(x, *popt_x)
gauss_y = gaussian(y, *popt_y)

gauss_x_scaled = gauss_x / np.max(gauss_x) * np.max(x_profile)
gauss_y_scaled = gauss_y / np.max(gauss_y) * np.max(y_profile)

print(popt_x)
print(popt_y)

# --- Plot
fig, axs = plt.subplots(2, 1, figsize=(12, 4))

axs[0].plot(x, x_profile, label="X profile")
axs[0].plot(x, gauss_x_scaled, 'k', label="Gaussian envelope (scaled)")
axs[0].set_title("X Profile with Gaussian Envelope")
axs[0].legend()

axs[1].plot(y, y_profile, label="Y profile")
axs[1].plot(y, gauss_y_scaled, 'k', label="Gaussian envelope (scaled)")
axs[1].set_title("Y Profile with Gaussian Envelope")
axs[1].legend()

plt.tight_layout()
plt.show()

