import os
import mss
import zerorpc
from rpc import Server, Client
from utils.get_sticks import get_sticks, save_sticks, Joystick
from utils.get_frames import get_monitor_params, get_frames, save_frames
from utils.json_helper import json_reader
from multiprocessing import Process, Queue
# from torch.multiprocessing import Process, Queue


def run_server(server_instance):
    s = zerorpc.Server(server_instance)
    s.bind("tcp://0.0.0.0:4242")
    s.run()


def set_daemon_true(p):
    p.daemon = True


class Manager(object):
    def __init__(self, args):
        # init sticks
        rc = Joystick()
        run = rc.status
        if args.sticks_calib_path == "":
            rc.calibrate(args.sticks_calib_path, load_calibration_file=False)
        else:
            if not os.path.exists(args.sticks_calib_path):
                raise FileNotFoundError("sticks_calib_path {} does not exist.".format(args.sticks_calib_path))
            rc.calibrate(args.sticks_calib_path, load_calibration_file=True)



        # init queues
        frame_queue = Queue()
        sticks_queue = Queue()

        # init processes
        # - init server
        server = Server(frame_queue, sticks_queue)
        server_p = Process(target=run_server, args=(server,))
        server_p.daemon = True
        server_p.start()

        # - init frame grabber
        get_frames_p = Process(target=get_frames, args=(frame_queue, args.monitor_number))
        set_daemon_true(get_frames_p)
        save_frames_p = [Process(target=save_frames, args=(frame_queue, args.path, args.png_compression)) for _ in range(args.num_workers)]
        [set_daemon_true(p) for p in save_frames_p]
        get_sticks_p = Process(target=get_sticks, args=(sticks_queue, rc))
        set_daemon_true(get_sticks_p)
        save_sticks_p = Process(target=save_sticks, args=(sticks_queue, args.path))
        set_daemon_true(save_sticks_p)

        # - init monitor
        if args.monitor_params_path == "":
            raise ValueError("monitor_params_path is emtpy. Where should the monitor_params file should be saved?!?")
        else:
            if not (os.path.splitext(args.monitor_params_path)[-1].split(".")[-1]=="json"): # path is missing json ext
                args.monitor_params_path = args.monitor_params_path + ".json"
            if os.path.exists(args.monitor_params_path): # monitor_params.json exists, load it.
                monitor_params = json_reader(args.monitor_params_path)
            else:                                        # monitor_params.json doesn't exist, create it.
                monitor_params = get_monitor_params()




