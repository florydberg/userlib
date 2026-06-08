import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from scipy.ndimage import gaussian_filter1d

# --- Load and process theory data from CSV ---
df = pd.read_csv("T13.csv")
df['I'] = abs(df['A'])  # or abs(df['A']) ** 2 if preferred

num_bins = 25
hist, bin_edges = np.histogram(df['x'], bins=num_bins, weights=df['I'])
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

# Gaussian convolution
sigma_bins = 2  # adjust sigma in bin units
hist_convoluted = gaussian_filter1d(hist, sigma=sigma_bins)

# Normalize both histograms
hist_norm = hist / np.max(hist)
hist_convoluted_norm = hist_convoluted / np.max(hist_convoluted)

# --- Load and process image profiles ---
def load_horizontal_profile(image_path):
    img = Image.open(image_path)
    img_array = np.array(img)
    if img_array.ndim == 3:  # convert to grayscale if RGB
        img_array = img_array.mean(axis=2)
    return img_array.mean(axis=0)  # average vertically

profile_original = load_horizontal_profile("original.tif")
profile_lut = load_horizontal_profile("LUT-ed.tif")

# Normalize image profiles
profile_original_norm = profile_original[50:220] / np.max(profile_original)
profile_lut_norm = profile_lut[50:220] / np.max(profile_lut)

# --- Rescale x-axis for comparison ---
x_image = np.linspace(0, 1, len(profile_original_norm))
x_theory = np.linspace(0, 1, len(hist_norm))

# --- Plot all profiles ---
plt.figure(figsize=(12, 6))
plt.plot(x_theory, hist_norm, label="Theory (Raw)", linewidth=2)
plt.plot(x_theory, hist_convoluted_norm, label="Theory (Gaussian Convoluted)", linewidth=2)
plt.plot(x_image, profile_original_norm, label="Original.tif", linestyle='--')
plt.plot(x_image, profile_lut_norm, label="LUT-ed.tiff", linestyle=':')

plt.xlabel("Normalized Horizontal Position")
plt.ylabel("Normalized Intensity")
plt.title("Comparison of Horizontal Intensity Profiles with Gaussian Convolution")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
