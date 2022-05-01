import mss
import cv2
import numpy as np
from time import time, perf_counter
import pyautogui

# SCREEN_SIZE = (1920, 1080)
# fource = cv2.VideoWriter_fourcc(*'XVID')
# out = cv2.VideoWriter('output.mp4', fource, 20.0, (SCREEN_SIZE))

# fps = 30
# prev = perf_counter()


def take_screenshots_pyautogui(n_frames):
    for i in range(n_frames):
        img = pyautogui.screenshot(region=(0,0, 1280, 720))


def take_screenshots_mss(n_frames):
    monitor_number = 1
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
        t0 = perf_counter()
        for i in range(n_frames):
            img_byte = sct.grab(monitor)
        t1 = perf_counter()
        print("{} fps".format(n_frames/(t1- t0)))

if __name__ == '__main__':
    n_frames = 100
    t0 = perf_counter()
    take_screenshots_mss(n_frames)

