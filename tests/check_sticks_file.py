import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

path = os.path.join(r"C:\Users\omrijsharon\Documents\fpv\tryp_rec", "sticks.csv")
df = pd.read_csv(path)
print("mean time between readings: ", np.diff(df["timestamp"].values).mean()*1e3, "ms")
print("std time between readings: ", np.diff(df["timestamp"].values).std(), "ms")
print("mean rps: ", 1 / np.diff(df["timestamp"].values).mean())
print("total time: ", df["timestamp"].values[-1] - df["timestamp"].values[0])
s = 20
alpha = 0.01
plt.subplot(1, 2, 1)
plt.scatter(df["yaw"].values, df["throttle"].values, s=s, linewidth=0, alpha=alpha)
plt.axis('square')
plt.xlim(-1, 1)
plt.ylim(-1, 1)
plt.subplot(1, 2, 2)
plt.scatter(df["roll"].values, df["pitch"].values, s=s, linewidth=0, alpha=alpha)
plt.axis('square')
plt.xlim(-1, 1)
plt.ylim(-1, 1)
plt.show()