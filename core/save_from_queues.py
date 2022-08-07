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


def save_frames_from_queue(queue_frames, path, stop_grab_event, resolution, type="png", compression=9):
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
        # sleep(0.05)
        timestamp, rgb = queue_frames.get()
        # print("q_size:", queue_frames.qsize())
        if stop_grab_event.is_set():
            print("Stopping frame saver pid ", os.getpid())
            break
        frame = np.frombuffer(rgb, np.uint8).reshape(resolution["height"], resolution["width"], 3)[:, :, ::-1]
        # filename = timestamp.strftime("%Y%m%d_%H%M%S.%f") + f".{type}"
        filename = str(timestamp).split(".")
        filename[1] = filename[1][::-1].zfill(6)[::-1]
        filename = "_".join(filename) + f".{type}"
        cv2.imwrite(os.path.join(path, filename), frame, type_compression)


def col_names(calib_file):
    calib = json_reader(calib_file)
    names = [""]*6
    for k, v in calib["sticks"].items():
        names[v["idx"]] = k
    for k, v in calib["switches"].items():
        names[v["idx"]] = k
    return names


def save_sticks_from_queue(queue_sticks, path, calib_file, stop_func, stop_grab_event, buffer_size=64):
    os.path.exists(path) or os.makedirs(path)
    shutil.copy2(calib_file, os.path.join(path, "calib_file.json"))
    df = pd.DataFrame(columns=["timestamp", *col_names(calib_file)])
    buffer = np.zeros(shape=(buffer_size, 1+6))
    i = 0
    counter = 0
    while True:
        timestamp, sticks = queue_sticks.get()
        if stop_func(sticks):
            counter += 1
            if counter > 10:
                print("Stopping sticks saver pid ", os.getpid())
                stop_grab_event.set()
                break
            # for _ in range(num_frame_workers):
            #     queue_frames.put((timestamp, None))

        buffer[i % buffer_size, 0] = timestamp
        buffer[i % buffer_size, 1:] = sticks.reshape(-1)
        i += 1
        if i % buffer_size == 0:
            df = pd.concat((df, pd.DataFrame(buffer, columns=["timestamp", *col_names(calib_file)], index=range(buffer_size))))
            df.to_csv(os.path.join(path, "sticks.csv"), index=False)
            i = 0
            # print("queue_rc size:", queue_rc.qsize())
    # when breaking out of the loop, save the last buffer
    buffer = buffer[:i % buffer_size, :]
    if len(buffer) > 0:
        df = pd.concat((df, pd.DataFrame(buffer, columns=["timestamp", *col_names(calib_file)], index=range(len(buffer)))))
        df.to_csv(os.path.join(path, "sticks.csv"), index=False)


def datetime_to_str(datetime_obj, strfmt="%Y%m%d%H%M%S%f"):
    return datetime_obj.strftime(strfmt)


def str_to_datetime(datetime_str, strfmt="%Y%m%d%H%M%S%f"):
    return datetime.strptime(datetime_str, "%Y%m%d%H%M%S%f")


if __name__ == '__main__':
    path = r'C:\Users\omrijsharon\Documents\fpv\tryp_rec'
    resolution = {"width": 1280, "height": 720}
    save_frames_from_queue(queue_frames, path, resolution, type="png", compression=6)