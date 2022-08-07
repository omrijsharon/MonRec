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
        stop_grab_event.clear()
        # init frame processes
        p_grab_frames = Process(target=grab_frames_to_queue, args=(queue_frames, stop_grab_event, resolution, 0))
        p_grab_frames.daemon = True
        p_save_frames = [Process(target=save_frames_from_queue, args=(queue_frames, path, stop_grab_event, resolution, type, compression)) for _ in range(num_workers)]
        # init stick processes
        p_grab_sticks = Process(target=grab_sticks_to_queue, args=(joystick, queue_sticks, stop_grab_event))
        p_grab_sticks.daemon = True
        p_save_sticks = Process(target=save_sticks_from_queue, args=(queue_sticks, path, calib_file, partial_stop_func, stop_grab_event, buffer_size))

        processes_list = [p_grab_frames, p_grab_sticks, p_save_sticks, *p_save_frames]

        # start processes
        [p.start() for p in processes_list]
        while stop_grab_event.is_set() is False:
            pass
        sleep(0.5)

        #stop processes and join
        [p.terminate() for p in processes_list if p.is_alive()]
        [p.kill() for p in processes_list if p.is_alive()]
        [p.join() for p in processes_list]
        [p.close() for p in processes_list]
        try:
            while not queue_frames.empty():
                queue_frames.get_nowait()
            while not queue_sticks.empty():
                queue_frames.get_nowait()
        except Exception as e:
            print(e)
        queue_frames.close()
        queue_sticks.close()
        full_summary(path)

    # TODO(omri): Add UI


if __name__ == '__main__':
    main()
    # print("start")
    # calib_file = r"C:\Users\omrijsharon\Documents\repos\MonRec\config\frsky.json"
    # from get_sticks import Joystick
    # rc = Joystick()
    # run = rc.status
    # rc.calibrate(calib_file, load_calibration_file=True)
    # calib_dict = json_reader(calib_file)
    # partial_stop_func = partial(stop_func, calib_dict=calib_dict, switch="switch1", stop_value=-1.0)
    # sleep(0.1)
    # readings = rc.calib_read()
    # print("stop? ", partial_stop_func(readings), readings[3])
    # while not partial_stop_func(readings):
    #     readings = rc.calib_read()
    #     rc.render_axes()
    # print("stop")

