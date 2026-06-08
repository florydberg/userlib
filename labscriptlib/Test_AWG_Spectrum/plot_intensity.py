import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load CSV file
df = pd.read_csv("T13.csv")  # Change path if needed

# Compute intensity: I = A^2
df['I'] = df['A'] ** 2

# Bin positions and accumulate intensity using histogram
num_bins = 500  # Adjust this for resolution
hist, bin_edges = np.histogram(df['x'], bins=num_bins, weights=df['I'])

# Calculate bin centers
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

# Compute cumulative sum for integrated intensity
cumulative_intensity = np.cumsum(hist)

# Plot cumulative (integrated) intensity profile
plt.figure(figsize=(10, 5))
plt.plot(bin_centers, cumulative_intensity, color='orange', label='Cumulative Intensity')
plt.xlabel("Position (µm)")
plt.ylabel("Cumulative Integrated Intensity")
plt.title("Cumulative Laser Intensity Over Position")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
