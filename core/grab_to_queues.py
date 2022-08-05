from multiprocessing import Process, Queue
import os
import mss
import mss.tools
from datetime import datetime
from time import perf_counter, sleep

from get_sticks import Joystick


def grab_frames_to_queue(queue_frames, resolution, monitor_number=0):
    with mss.mss() as sct:
        mon = sct.monitors[monitor_number]
        monitor_middle = dict(width=int(mon["width"] / 2), height=int(mon["height"] / 2))
        resolution_middle = dict(width=int(resolution["width"] / 2), height=int(resolution["height"] / 2))
        monitor = {
            "top": monitor_middle["height"] - resolution_middle["height"]-20,
            "left": monitor_middle["width"] - resolution_middle["width"],
            "width": resolution["width"],
            "height": resolution["height"],
            "mon": monitor_number,
        }
        # while True:
        for i in range(500):
            # img_byte = sct.grab(monitor)
            queue_frames.put_nowait((datetime.now().timestamp(), sct.grab(monitor).rgb))
            # img = np.frombuffer(img_byte.rgb, np.uint8).reshape(monitor["height"], monitor["width"], 3)[:, :, ::-1]
            # cv2.imshow("Output", img)
            # k = cv2.waitKey(1)
            # if k == 27:  # Esc key to stop
            #     break


def grab_sticks_to_queue(queue_sticks):
    rc = Joystick()
    run = rc.status
    rc.calibrate(r"C:\Users\omrijsharon\Documents\repos\MonRec\config\frsky.json", load_calibration_file=True)
    while True:
        queue_sticks.put_nowait((datetime.now().timestamp(), rc.calib_read()))
        sleep(1e-6)


if __name__ == '__main__':
    q = Queue()
    grab_sticks_to_queue(q)