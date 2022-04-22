import os.path

import cv2
import numpy as np
from time import time
import mss.tools
from multiprocessing import Process, Queue
# from torch.multiprocessing import Process, Queue


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
            frame_queue.put_nowait([time(), sct.grab(monitor)])


def save_frames(frame_queue, path, level=6):
    while True:
        t, sct_img = frame_queue.get()
        mss.tools.to_png(sct_img.rgb, sct_img.size, level=level, output=os.path.join(path, frame_filename(t, sct_img)))


def frame_to_numpy(frame, monitor):
    img = np.frombuffer(frame.rgb, np.uint8).reshape(monitor["height"], monitor["width"], 3)[:, :, ::-1]
    return img

