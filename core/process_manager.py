import os
import numpy as np
from multiprocessing import Process, Queue, Event
from grab_to_queues import grab_frames_to_queue, grab_sticks_to_queue
from save_from_queues import save_frames_from_queue, save_sticks_from_queue
from time import sleep
from datetime import datetime
from functools import partial
from tqdm import tqdm
from utils.json_helper import json_reader
from utils.record_summary import full_summary
from get_sticks import Joystick


def stop_func(calib_readings, calib_dict, switch: str, stop_value: float):
    idx = calib_dict['switches'][switch]["idx"]
    return calib_readings[idx] == stop_value


def terminate_queues(queues: list):
    try:
        for queue in queues:
            while not queue.empty():
                queue.get_nowait()
    except Exception as e:
        print(e)
    [queue.close() for queue in queues]


def terminate_processes(processes: list):
    [p.terminate() for p in processes if p.is_alive()]
    [p.kill() for p in processes if p.is_alive()]
    [p.join() for p in processes]
    [p.close() for p in processes]


def main():
    # Parameters
    resolution = {'width': 1280, 'height': 720}
    num_workers = 2
    buffer_size = 64
    base_path = r'C:\Users\omrijsharon\Documents\fpv\tryp_rec'
    calib_file = r"C:\Users\omrijsharon\Documents\repos\MonRec\config\frsky.json"
    calib_dict = json_reader(calib_file)
    stop_switch = "switch1"
    stop_value = -1.0
    partial_stop_func = partial(stop_func, calib_dict=calib_dict, switch=stop_switch, stop_value=stop_value)
    quit_switch = "switch2"
    quit_value = 1.0
    partial_quit_func = partial(stop_func, calib_dict=calib_dict, switch=quit_switch, stop_value=quit_value)
    type = "jpg"
    compression = 70

    stop_grab_event = Event()
    # sticks initialization
    joystick = Joystick()
    run = joystick.status
    joystick.calibrate(calib_file, load_calibration_file=True)

    for r in range(3):
        queue_frames = Queue()
        queue_sticks = Queue()
        stop_grab_event.clear()
        path = os.path.join(base_path, datetime.now().strftime("%Y%m%d_%H%M%S"))
        counter = 0
        quit = False
        while counter < 10:
            counter += 1 * (not partial_stop_func(joystick.calib_read()))
            quit = partial_quit_func(joystick.calib_read())
            if quit:
                break
        if quit:
            break
        sleep(1)
        print("Start recording #{}".format(r))
        print("path:  ", path)

        # init processes
        p_grab_frames = Process(target=grab_frames_to_queue, args=(queue_frames, stop_grab_event, resolution, 0), daemon=True)
        p_grab_sticks = Process(target=grab_sticks_to_queue, args=(joystick, queue_sticks, stop_grab_event), daemon=True)
        p_save_sticks = Process(target=save_sticks_from_queue, args=(queue_sticks, path, calib_file, partial_stop_func, stop_grab_event, buffer_size))
        p_save_frames = [Process(target=save_frames_from_queue, args=(queue_frames, path, stop_grab_event, resolution, type, compression)) for _ in range(num_workers)]
        processes_list = [p_grab_frames, p_grab_sticks, p_save_sticks, *p_save_frames]

        # start processes
        [p.start() for p in processes_list]

        # wait for processes to get a kill switch.
        while stop_grab_event.is_set() is False:
            pass
        sleep(0.5)

        terminate_processes(processes_list)
        terminate_queues([queue_frames, queue_sticks])
        full_summary(path)

    # TODO(omri): Add UI


if __name__ == '__main__':
    main()
