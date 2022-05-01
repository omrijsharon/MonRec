import os.path
import json
import tkinter as tk
from tkinter import ttk
from tkinter import StringVar
from functools import partial
import cv2
import numpy as np
from time import time
import mss
import mss.tools
from multiprocessing import Process, Queue
# from torch.multiprocessing import Process, Queue
from utils.json_helper import json_writer, json_reader


def get_monitor_ui():
    sct = mss.mss()

    root = tk.Tk()
    mon = StringVar()

    def kill(n):
        mon.set(n)
        root.quit()

    root.geometry("140x150")
    buttons = []
    for i, m in enumerate(sct.monitors):
        s = "monitor #{}, {}x{}".format(i, m["height"], m["width"])
        buttons.append(ttk.Button(root, text=s, command=partial(kill, n=len(buttons))))
        buttons[-1].pack()

    root.mainloop()
    return mon.get()


def get_monitor_params(monitor_number=None, path=None):
    if path is None:
        if monitor_number is None:
            monitor_number = get_monitor_ui()
        raise NotImplementedError
    else:
        return json_reader(path)


def save_monitor_params(monitor_params, path):
    json_writer(monitor_params, path)


def frame_filename(t, sct_img):
    return "ts_{}_sct_{top}x{left}_{width}x{height}.png"\
        .format(str(t).replace(".", "_"), sct_img.top, sct_img.left, sct_img.width, sct_img.height)


def get_frames(frame_queue, monitor_number):
    with mss.mss() as sct:
        # Get information of monitor 2
        mon = sct.monitors[monitor_number]
        # The screen part to capture
        monitor = {
            "top": mon["top"] + 200,  # 100px from the top
            "left": mon["left"] + 200,  # 100px from the left
            "width": int(1280),
            "height": int(720),
            "mon": monitor_number,
        }
        while True:
            img_byte = sct.grab(monitor)
            frame_queue.put_nowait([time(), img_byte])
            if sum(img_byte.pixels[0][0]) == 0: #@TODO: SLOW!!!!
                break


def save_frames(frame_queue, path, level=6):
    while True:
        t, sct_img = frame_queue.get()
        mss.tools.to_png(sct_img.rgb, sct_img.size, level=level, output=os.path.join(path, frame_filename(t, sct_img)))


def frame_to_numpy(frame, monitor):
    img = np.frombuffer(frame.rgb, np.uint8).reshape(monitor["height"], monitor["width"], 3)[:, :, ::-1]
    return img

if __name__ == '__main__':
    get_monitor_ui()