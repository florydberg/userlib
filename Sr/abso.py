import numpy as np
import matplotlib.pyplot as plt
from scipy import ndimage
from skimage import io
import tifffile as tf

# Load the TIFF file containing the three images
tif_file_path = 'bibo.tif'
images = io.imread(tif_file_path)

# Extract the three images (assuming they are stacked in the TIFF file)
absorption = images[0]
beam = images[1]
background = images[2]

# Define the constant 'c'
c = 1.0

# Perform the operation: c * log((absorption - background) / (beam - background))
result_image = c * np.log((absorption - background) / (beam - background))

# Display the result image
plt.figure(figsize=(8, 8))
plt.imshow(result_image, cmap='gray')
plt.colorbar()
plt.title('Result Image')
plt.show()