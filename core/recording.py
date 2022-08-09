import os
import numpy as np
from tkinter import messagebox

from multiprocessing import Process, Queue, Event
from grab_to_queues import grab_frames_to_queue, grab_sticks_to_queue
from save_from_queues import save_frames_from_queue, save_sticks_from_queue
from time import sleep
from datetime import datetime
from utils.json_helper import json_reader, json_writer
from utils.record_summary import full_summary
from get_sticks import Joystick

from functools import partial


class RecordingManager:
    def __init__(self, joystick, config, stop_grab_event):
        self.config = config
        self.resolution = config.get("resolution")
        self.compression = config.get("compression")
        self.type = config.get("type")
        self.num_workers = config.get("num_workers")
        self.calib_file = config.get("calib_file")
        self.buffer_size = config.get("buffer_size")
        self.base_path = config.get("rec_dir")
        self.joystick = joystick
        self.stop_grab_event = stop_grab_event
        self.is_recording = False
        self.queue_frames = None
        self.queue_sticks = None
        self.p_grab_frames = None
        self.p_grab_sticks = None
        self.p_save_sticks = None
        self.p_save_frames = None
        self.path = None

    def update_config(self, config):
        self.config = config
        self.resolution = config.get("resolution")
        self.compression = config.get("compression")
        self.type = config.get("type")
        self.num_workers = config.get("num_workers")
        self.calib_file = config.get("calib_file")
        self.buffer_size = config.get("buffer_size")
        self.base_path = config.get("rec_dir")

    def get_a_path(self):
        return os.path.join(self.base_path, datetime.now().strftime("%Y%m%d_%H%M%S"))

    def reset(self):
        self.path = self.get_a_path()
        #init queues
        self.queue_frames = Queue()
        self.queue_sticks = Queue()
        # init processes
        self.p_grab_frames = Process(target=grab_frames_to_queue, args=(self.queue_frames, self.stop_grab_event, self.resolution, self.compression, 0), daemon=True)
        self.p_grab_sticks = Process(target=grab_sticks_to_queue, args=(self.joystick, self.queue_sticks, self.stop_grab_event), daemon=True)
        self.p_save_sticks = Process(target=save_sticks_from_queue, args=(self.queue_sticks, self.path, self.calib_file, self.stop_grab_event, self.buffer_size))
        self.p_save_frames = [Process(target=save_frames_from_queue, args=(self.queue_frames, self.path, self.stop_grab_event, self.resolution, self.type, self.compression)) for _ in range(self.num_workers)]

    def start_recording(self):
        if not os.path.exists(self.calib_file):
            messagebox.showerror("Error", "Calibration file not found")
            return None
        self.reset()
        os.path.exists(self.path) or os.makedirs(self.path)
        sleep(1)
        print("Start recording to:  ", self.path)
        processes_list = [self.p_grab_frames, self.p_grab_sticks, self.p_save_sticks, *self.p_save_frames]
        # start processes
        [p.start() for p in processes_list]
        self.is_recording = True

    def stop_recording(self):
        if self.is_recording:
            self.terminate_processes()
            self.terminate_queues()
            self.is_recording = False
            full_summary(self.path)
        else:
            messagebox.showerror("Error", "No recording in progress")

    def terminate_queues(self):
        queues = [self.queue_frames, self.queue_sticks]
        try:
            for queue in queues:
                while not queue.empty():
                    queue.get_nowait()
        except Exception as e:
            print(e)
        [queue.close() for queue in queues]

    def terminate_processes(self):
        processes = [self.p_grab_frames, self.p_grab_sticks, self.p_save_sticks, *self.p_save_frames]
        [p.terminate() for p in processes if p.is_alive()]
        [p.kill() for p in processes if p.is_alive()]
        [p.join() for p in processes]
        [p.close() for p in processes]


def stop_func(calib_readings, calib_dict, switch: str, stop_value: float):
    idx = calib_dict['switches'][switch]["idx"]
    return calib_readings[idx] == stop_value


def start_recording(joystick, config, btn_start_recording, stop_grab_event):
    stop_grab_event.clear()
    # Initialize queues
    queue_frames = Queue()
    queue_sticks = Queue()

    # Parameters
    resolution = config["resolution"]
    num_workers = config["num_workers"]
    buffer_size = config["buffer_size"]
    base_path = config["rec_dir"]
    type = config["type"]
    compression = config["compression"]
    calib_file = config["calib_file"]
    if not os.path.exists(calib_file):
        messagebox.showerror("Error", "Calibration file not found")
        return None
        # btn_start_recording["text"] = "Start Recording"
        # stop_grab_event.set()

    path = os.path.join(base_path, datetime.now().strftime("%Y%m%d_%H%M%S"))
    sleep(1)
    print("path:  ", path)

    # init processes
    p_grab_frames = Process(target=grab_frames_to_queue,
                            args=(queue_frames, stop_grab_event, resolution, compression, 0), daemon=True)
    p_grab_sticks = Process(target=grab_sticks_to_queue, args=(joystick, queue_sticks, stop_grab_event), daemon=True)
    p_save_sticks = Process(target=save_sticks_from_queue,
                            args=(queue_sticks, path, calib_file, stop_grab_event, buffer_size))
    p_save_frames = [Process(target=save_frames_from_queue,
                             args=(queue_frames, path, stop_grab_event, resolution, type, compression)) for _ in
                     range(num_workers)]
    processes_list = [p_grab_frames, p_grab_sticks, p_save_sticks, *p_save_frames]

    queues_list = [queue_frames, queue_sticks]
    partial_stop_recording = partial(stop_recording, processes_list, queues_list, btn_start_recording, path, joystick, config, stop_grab_event)
    btn_start_recording["text"] = "Stop Recording"
    btn_start_recording["command"] = partial_stop_recording

    # start processes
    [p.start() for p in processes_list]

    # wait for processes to get a kill switch.
    while stop_grab_event.is_set() is False:
        pass
    sleep(0.5)

    terminate_processes(processes_list)
    terminate_queues([queue_frames, queue_sticks])
    full_summary(path)
    btn_start_recording["text"] = "Start Recording"


def stop_recording(processes_list, queues_list, btn_start_recording, path, joystick, config, stop_grab_event):
    btn_start_recording["text"] = "Start Recording"
    partial_start_recording = partial(start_recording, joystick, config, btn_start_recording, stop_grab_event)
    btn_start_recording.config(command=partial_start_recording)
    terminate_processes(processes_list)
    terminate_queues(queues_list)
    full_summary(path)


def init_joystick(config):
    joystick = Joystick()
    run = joystick.status
    joystick.calibrate(config.get("calib_file"), load_calibration_file=True)
    return joystick


def listen2sticks(config, joystick, stop_grab_event: Event, listener_killer_event: Event):
    print("listen2sticks")
    calib_dict = json_reader(config.get("calib_file"))
    stop_switch = "switch1"
    stop_value = -1.0
    partial_stop_func = partial(stop_func, calib_dict=calib_dict, switch=stop_switch, stop_value=stop_value)
    # quit_switch = "switch2"
    # quit_value = 1.0
    # partial_quit_func = partial(stop_func, calib_dict=calib_dict, switch=quit_switch, stop_value=quit_value)
    while True:
        readings = joystick.calib_read()
        if partial_stop_func(readings) and stop_grab_event.is_set() is False: # joystick said stop, event not stopped yet
            stop_grab_event.set() # so stop
            print("Stop")
        elif not partial_stop_func(readings) and stop_grab_event.is_set() is True: # joystick said start, event is stoppped
            stop_grab_event.clear() # so start
            print("Start")
        if listener_killer_event.is_set():
            break
        sleep(0.01)
