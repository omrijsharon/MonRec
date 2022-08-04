import os
import cv2
from multiprocessing import Process, Queue
from datetime import datetime
from time import sleep
import numpy as np
import shutil
import pandas as pd

from utils.json_helper import json_reader
from get_sticks import Joystick

queue_rc = Queue()
queue_frames = Queue()


def save_frames_from_queue(queue_frames, path, type="png", compression=9):
    assert isinstance(compression, int), "compression must be an integer."
    if type == "png":
        assert 9 >= compression >= 0, "png compression must be between 0 and 9."
        type_compression = [int(cv2.IMWRITE_PNG_COMPRESSION), compression]
    elif type == "jpg" or type == "jpeg":
        assert 100 >= compression >= 0, "jpg compression must be between 0 and 100."
        type_compression = [int(cv2.IMWRITE_JPEG_QUALITY), compression]
    else:
        raise ValueError("type must be either 'png' or 'jpg'.")
    os.path.exists(path) or os.makedirs(path)
    while True:
        timestamp, frame = queue_frames.get()
        if frame is None:
            break
        filename = timestamp.strftime("%Y%m%d_%H%M%S.%f") + ".png"
        cv2.imwrite(os.path.join(path, filename), frame, type_compression)


def col_names(calib_file):
    calib = json_reader(calib_file)
    names = [""]*6
    for k, v in calib["sticks"].items():
        names[v["idx"]] = k
    for k, v in calib["switches"].items():
        names[v["idx"]] = k
    return names


def save_sticks_from_queue(queue_rc, path, calib_file, stop_func, queue_frames, buffer_size=64):
    os.path.exists(path) or os.makedirs(path)
    shutil.copy2(calib_file, os.path.join(path, "calib_file.json"))
    df = pd.DataFrame(columns=["timestamp", *col_names(calib_file)])
    buffer = np.zeros(shape=(buffer_size, 1+6))
    i = 0
    while True:
        timestamp, sticks = queue_rc.get()
        if stop_func(sticks) is True:
            queue_frames.put((timestamp, None))
            break
        buffer[i % buffer_size, 0] = timestamp.timestamp()
        buffer[i % buffer_size, 1:] = sticks.reshape(-1)
        i += 1
        if i % buffer_size == 0:
            df = df.append(pd.DataFrame(buffer, columns=["timestamp", *col_names(calib_file)], index=range(buffer_size)))
            df.to_csv(os.path.join(path, "sticks.csv"), index=False)
            i = 0
    # when breaking out of the loop, save the last buffer
    buffer = buffer[:i % buffer_size, :]
    df = df.append(pd.DataFrame(buffer, columns=["timestamp", *col_names(calib_file)], index=range(buffer_size)))
    df.to_csv(os.path.join(path, "sticks.csv"), index=False)


def datetime_to_str(datetime_obj, strfmt="%Y%m%d%H%M%S%f"):
    return datetime_obj.strftime(strfmt)


def str_to_datetime(datetime_str, strfmt="%Y%m%d%H%M%S%f"):
    return datetime.strptime(datetime_str, "%Y%m%d%H%M%S%f")


if __name__ == '__main__':
    rc = Joystick()
    run = rc.status
    calib_file = r'C:\Users\omrijsharon\Documents\repos\MonRec\config\frsky.json'
    rc.calibrate(calib_file, load_calibration_file=True)
    buffer_size = 64
    df = pd.DataFrame(columns=["timestamp", *col_names(calib_file)], index=range(buffer_size))
    buffer = np.zeros(shape=(buffer_size, 1 + 6))
    for i in range(buffer_size):
        readings = rc.calib_read()
        buffer[i, 0] = datetime.now().timestamp()
        buffer[i, 1:] = readings
        sleep(1e-3)
    df.loc[:] = buffer