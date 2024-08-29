import math 
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd



file_path = 'SDS00001.csv'  # Replace with your CSV file path
df = pd.read_csv(file_path)

df_data = df.to_json(orient= 'table')


plt.rcParams["figure.figsize"] = [7.50, 3.50]
plt.rcParams["figure.autolayout"] = True

headers = ['Time', 'Ch1', 'Ch2']

df = pd.read_csv('SDS00001.csv', names=headers)

print(df)
df.set_index('Time').plot()

plt.show()