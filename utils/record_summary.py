import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tabulate import tabulate
from tkinter import messagebox


def frames_summary(path):
    # path = r'C:\Users\omrijsharon\Documents\fpv\tryp_rec'
    img_files = [filename for filename in os.listdir(path) if filename.split(".")[1]=="jpg"]
    if len(img_files) == 0:
        raise FileNotFoundError(f"No Frames Found in {path}")
    x = np.array([float(filename.split(".")[0].replace("_",".")) for filename in img_files])
    fps = 1/np.mean(np.diff(x))
    mean = np.mean(np.diff(x)*1e3)
    std = np.std(np.diff(x)*1e3)
    total_frames = len(img_files)
    total_time = x[-1]-x[0]
    return fps, mean, std, total_frames, total_time


def sticks_summary(path, plot=False):
    path = os.path.join(path, "sticks.csv")
    df = pd.read_csv(path)
    rps = 1 / np.diff(df["timestamp"].values).mean()
    mean = np.diff(df["timestamp"].values).mean() * 1e3
    std = np.diff(df["timestamp"].values).std() * 1e3
    total_readings = len(df["timestamp"].values)
    total_time = df["timestamp"].values[-1] - df["timestamp"].values[0]
    if plot:
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
    return rps, mean, std, total_readings, total_time


def full_summary(path, plot=False):
    headers = ["FPS", "Mean [ms]", "std [ms]", "num", "Total time [sec]"]
    # print("\nFull summary:\n----------------")
    try:
        fps, frames_mean, frames_std, total_frames, frames_total_time = frames_summary(path)
        rps, sticks_mean, sticks_std, total_readings, sticks_total_time = sticks_summary(path, plot)
        data = [["frames", fps, frames_mean, frames_std, total_frames, frames_total_time],
                ["sticks", rps, sticks_mean, sticks_std, total_readings, sticks_total_time]]
        # print(tabulate(data, headers=headers))
        # messagebox.showinfo("Summary", tabulate(data, headers=headers))
    except Exception as e:
        print(e)
        data = [["frames", "N/A", "N/A", "N/A", "N/A", "N/A"],
                ["sticks", "N/A", "N/A", "N/A", "N/A", "N/A"]]
        # messagebox.showerror("Summary", tabulate(data, headers=headers))
    return data, headers