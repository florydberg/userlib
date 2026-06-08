import pandas as pd
import matplotlib.pyplot as plt

# === Replace this path with your actual CSV file path ===
csv_file = 'T13.csv'  # or provide full path like '/path/to/T13.csv'

# Load the data
df = pd.read_csv(csv_file)

# Plotting
plt.figure(figsize=(10, 5))

# Plot x(t)
plt.subplot(2, 1, 1)
plt.plot(df['t'], df['x'], label='x(t)', color='blue')
plt.ylabel('x (μm)')
plt.title('Andamento di x(t) e y(t)')
plt.grid(True)
plt.legend()

# Plot y(t)
plt.subplot(2, 1, 2)
plt.plot(df['t'], df['y'], label='y(t)', color='green')
plt.xlabel('Tempo (s)')
plt.ylabel('y (μm)')
plt.grid(True)
plt.legend()

plt.tight_layout()
plt.show()
