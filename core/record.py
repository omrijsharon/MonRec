import zerorpc
import numpy as np
from time import sleep, time, perf_counter
import mss
import mss.tools
import cv2
from multiprocessing import Process, Queue
# from torch.multiprocessing import Process, Queue
from utils.get_sticks import get_sticks, save_sticks, Joystick
from utils.get_frames import get_frames, save_frames


class Manager:
    def __init__(self, frames_queue, sticks_queue):
        rc = Joystick()
        run = rc.status
        rc.calibrate("frsky.json", load_calibration_file=True)
        



    def hello(self, name):
        return "Hello, %s" % name


frames_queue = Queue()
sticks_queue = Queue()
s = zerorpc.Server(Manager(frames_queue, sticks_queue))
s.bind("tcp://0.0.0.0:4242")
s.run()


def start_recording(args):

        rc = Joystick()
        run = rc.status
        rc.calibrate("frsky.json", load_calibration_file=True)

        frame_queue = Queue()
        sticks_queue = Queue()
        get_frames_p = Process(target=get_frames, args=(frame_queue, args.monitor_number))
        get_frames_p.daemon = True
        save_frames_p = Process(target=save_frames, args=(frame_queue, args.path, args.png_compression))
        save_frames_p.daemon = True
        get_sticks_p = Process(target=get_sticks, args=(sticks_queue, rc))
        get_sticks_p.daemon = True
        save_sticks_p = Process(target=save_sticks, args=(sticks_queue, args.path))
        save_sticks_p.daemon = True
        get_frames_p.start()
        get_sticks_p.start()
        save_frames_p.start()
        save_sticks_p.start()
