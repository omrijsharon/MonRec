import mss
import zerorpc
from utils.get_sticks import get_sticks, save_sticks, Joystick
from utils.get_frames import get_monitor_params, get_frames, save_frames
from multiprocessing import Process, Queue
# from torch.multiprocessing import Process, Queue


class Server:
    def __init__(self, frames_queue, sticks_queue):
        self.frames_queue = frames_queue
        self.sticks_queue = sticks_queue

    def start_recording(self, ):
        pass
        # get_frames(self.frames_queue, monitor_number=1)
        # get_sticks(self.sticks_queue, rc=)


def run_server(server_instance, ip='0.0.0.0', port='4242'):
    s = zerorpc.Server(server_instance)
    s.bind("tcp://{}:{}".format(ip, port))
    s.run()