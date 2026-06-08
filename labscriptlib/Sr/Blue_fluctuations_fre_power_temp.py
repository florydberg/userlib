import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ----------------------------
# PARAMETRI
# ----------------------------
csv_path = "C:\\Copy of temperature_461nm_19_12_2025_box_transient.csv"

# ----------------------------
# LETTURA FILE
# ----------------------------
df = pd.read_csv(csv_path)

time = df["time"].values
power = df["power"].values


# PLOT
# ----------------------------
plt.figure(figsize=(9, 6))

plt.subplot(2, 1, 1)
plt.plot(time, power)
plt.axhline(power_mean, linestyle="--")
plt.ylabel("Potenza")
plt.title("Potenza vs Tempo")

plt.subplot(2, 1, 2)
plt.plot(time, delta_power)
plt.ylabel("Δ Potenza")
plt.xlabel("Tempo [s]")
plt.title("Fluttuazioni di potenza")

plt.tight_layout()
plt.show()
