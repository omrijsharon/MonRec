import numpy as np
import os

path = r'C:\Users\omrijsharon\Documents\fpv\tryp_rec'
img_files = [filename for filename in os.listdir(path) if filename.split(".")[1]=="jpg"]
x = np.array([float(filename.split(".")[0].replace("_",".")) for filename in img_files])
print("FPS: ", 1/np.mean(np.diff(x)))
print(np.mean(np.diff(x)*1e3))
print(np.std(np.diff(x)*1e3))
print("total time: ", x[-1]-x[0])