import numpy as np
from multiprocessing import Process, Queue
from grab_to_queues import grab_frames_to_queue, grab_sticks_to_queue
from save_from_queues import save_frames_from_queue, save_sticks_from_queue
from time import sleep
from functools import partial

from utils.json_helper import json_reader


def stop_func(calib_readings, calib_dict, switch: str, stop_value: float):
    idx = calib_dict['switches'][switch]["idx"]
    return calib_readings[idx] == stop_value


def main():
    # define queues
    queue_frames = Queue()
    queue_sticks = Queue()

    # Parameters
    resolution = {'width': 1280, 'height': 720}
    num_workers = 2
    buffer_size = 64
    path = r'C:\Users\omrijsharon\Documents\fpv\tryp_rec'
    calib_file = r"C:\Users\omrijsharon\Documents\repos\MonRec\config\frsky.json"
    calib_dict = json_reader(calib_file)
    partial_stop_func = partial(stop_func, calib_dict=calib_dict, switch="switch1", stop_value=-1.0)
    type = "jpg"
    compression = 70

    # init processes
    p_grab_frames = Process(target=grab_frames_to_queue, args=(queue_frames, resolution, 0))
    p_save_frames = [Process(target=save_frames_from_queue, args=(queue_frames, path, resolution, type, compression)) for _ in range(num_workers)]
    p_grab_sticks = Process(target=grab_sticks_to_queue, args=(queue_sticks,))
    p_save_sticks = Process(target=save_sticks_from_queue, args=(queue_sticks, path, calib_file, partial_stop_func, queue_frames, num_workers, buffer_size))

    # start processes
    [p.start() for p in p_save_frames]
    p_save_sticks.start()
    p_grab_frames.start()
    p_grab_sticks.start()

    sleep(60)

    # stop processes
    p_grab_frames.terminate()
    p_grab_sticks.terminate()
    print("queue_frames.qsize() : ", queue_frames.qsize(), "      queue_sticks.qsize() : ", queue_sticks.qsize())
    queue_sticks.put_nowait((None, np.ones(6)))
    # [queue_frames.put((None, None)) for _ in range(num_workers)]

    # wait for processes to finish
    [p.join() for p in p_save_frames]
    print("queue_frames.qsize() : ", queue_frames.qsize(), "      queue_sticks.qsize() : ", queue_sticks.qsize())
    # save_sticks_from_queue(sticks_queue)
    p_grab_frames.join()

    # TODO(omri): Test sticks recording and reading from file
    # TODO(omri): Empty the queues and check when to start recording again
    # TODO(omri): Check when to quit the program (using the other switch)
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

