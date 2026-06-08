import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image


min=50
max=222
# --- Load and process theory data from CSV ---
df = pd.read_csv("T13.csv")
df['I'] = abs(df['A'])  # or abs(df['A']) ** 2 if you prefer squared intensity
num_bins = 25
hist, bin_edges = np.histogram(df['x'], bins=num_bins, weights=df['I'])
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

# Normalize theory intensity
hist_norm = hist / np.max(hist)

# --- Load and process image profiles ---
def load_horizontal_profile(image_path):
    img = Image.open(image_path)
    img_array = np.array(img)
    if img_array.ndim == 3:  # convert to grayscale if RGB
        img_array = img_array.mean(axis=2)
    return img_array.mean(axis=0)  # average vertically

profile_original = load_horizontal_profile("5x5tweezers_23.tif")
profile_lut = load_horizontal_profile("5x5tweezers_24.tif")

# Normalize image profiles
profile_original_norm = profile_original / np.max(profile_original)
profile_lut_norm = profile_lut / np.max(profile_lut)

# Resize theoretical data to match image profiles' horizontal length
x_image = np.linspace(0, 1, len(profile_original_norm[min : max]))
x_theory = np.linspace(0, 1, len(hist_norm))  # normalize x for comparison

# --- Plot all three profiles ---
plt.figure(figsize=(12, 6))
# plt.plot(x_theory, hist_norm, label="Theory (T13.csv)", linewidth=2)
plt.plot(x_image, profile_original_norm[min : max], "y", label="Original.tif", linestyle='--')
plt.plot(x_image, profile_lut_norm[min : max], "g", label="LUT-ed.tiff", linestyle=':')
plt.ylim([0,1.2])

plt.xlabel("Normalized Horizontal Position")
plt.ylabel("Normalized Intensity")
plt.title("Comparison of Horizontal Intensity Profiles")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
