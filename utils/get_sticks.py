# TODO: not updated. do not use!
# https://github.com/Rabbid76/python_windows_joystickapi
import joystickapi
import numpy as np
import os
import json
from time import time, sleep
import matplotlib.pyplot as plt
from drawnow import drawnow
from tqdm import tqdm
from utils.json_helper import json_writer, json_reader


class Joystick:
    def __init__(self):
        num = joystickapi.joyGetNumDevs()
        ret, caps, startinfo = False, None, None
        for id_num in range(num):
            ret, caps = joystickapi.joyGetDevCaps(id_num)
            if ret:
                print("gamepad detected: " + caps.szPname)
                ret, self.startinfo = joystickapi.joyGetPosEx(id_num)
                break
        else:
            print("no gamepad detected")
        self.id_num = id_num
        self.btns = None
        self.ret = ret
        self.caps = caps
        self.calib = False
        self.axisXYZ = None
        self.axisRUV = None

    @property
    def status(self):
        return self.ret

    def read(self, with_buttons=False):
        self.ret, info = joystickapi.joyGetPosEx(self.id_num)
        self.axisXYZ = [info.dwXpos-self.startinfo.dwXpos, info.dwYpos-self.startinfo.dwYpos, info.dwZpos-self.startinfo.dwZpos]
        self.axisRUV = [info.dwRpos-self.startinfo.dwRpos, info.dwUpos-self.startinfo.dwUpos, info.dwVpos-self.startinfo.dwVpos]
        if with_buttons:
            self.btns = [(1 << i) & info.dwButtons != 0 for i in range(self.caps.wNumButtons)]
        return {"axes": [*self.axisXYZ, *self.axisRUV], "buttons": self.btns}

    def make_fig_bars(self):
        k = 1
        if self.btns is not None:
            k = 2
            plt.subplot(k, 1, 2)
            plt.imshow(np.array(self.btns, dtype=int).reshape(1, -1))
        plt.subplot(k, 1, 1)
        plt.bar(['X', 'Y', 'Z', 'R', 'U', 'V'], [*self.axisXYZ, *self.axisRUV])
        plt.ylim(-32767, 32767)

    def make_fig_axes(self):
        alpha = 0.2
        plt.subplot(1, 2, 1)
        plt.plot([-1, 1], [0, 0], 'b', lw=3, alpha=alpha)
        plt.plot([0, 0], [-1, 1], 'b', lw=3, alpha=alpha)
        plt.scatter(self.calib_reading[self.sticks["yaw"]["idx"]], self.calib_reading[self.sticks["throttle"]["idx"]])
        plt.axis('square')
        plt.xlim(-1, 1)
        plt.ylim(-1, 1)
        plt.subplot(1, 2, 2)
        plt.plot([-1, 1], [0, 0], 'b', lw=3, alpha=alpha)
        plt.plot([0, 0], [-1, 1], 'b', lw=3, alpha=alpha)
        plt.scatter(self.calib_reading[self.sticks["roll"]["idx"]], self.calib_reading[self.sticks["pitch"]["idx"]])
        plt.axis('square')
        plt.xlim(-1, 1)
        plt.ylim(-1, 1)

    def render_bars(self):
        drawnow(self.make_fig_bars)

    def render_axes(self):
        drawnow(self.make_fig_axes)

    def calibrate(self, calibration_file_path, load_calibration_file=True):
        def record(t_sec, rps=100, text=None):
            if text is not None:
                print(text)
            readings = np.array(self.read(with_buttons=False)["axes"]).reshape(1, -1)
            for _ in tqdm(range(t_sec * rps)):
                readings = np.vstack((readings, np.array(self.read(with_buttons=False)["axes"]).reshape(1, -1)))
                sleep(1 / rps)
            return readings

        def norm_record(t_sec, rps=100, text=None):
            if text is not None:
                print(text)
            readings = np.array(self.norm_read()).reshape(1, -1)
            for _ in tqdm(range(t_sec * rps)):
                readings = np.vstack((readings, np.array(self.norm_read()).reshape(1, -1)))
                sleep(1 / rps)
            return readings

        def get_center(readings):
            for i in range(2, len(readings)):
                if readings[-i:].std(axis=0).mean() > 1e-16:
                    break
            return readings[-i + 1:].mean(axis=0)

        if load_calibration_file and os.path.isfile(calibration_file_path):
            calib_file = json_reader(calibration_file_path)
            self.active_axes = np.array(calib_file["active_axes"])
            self.min_vals = np.array(calib_file["min_vals"])
            self.max_vals = np.array(calib_file["max_vals"])
            self.sticks = calib_file["sticks"]

        elif load_calibration_file and not os.path.isfile(calibration_file_path):
            raise FileNotFoundError("Calibration file does not exist. Calibration path given: {}".format(calibration_file_path))

        else:
            # Check which sticks move
            print("\nmove the sticks around")
            readings = record(t_sec=5)
            self.active_axes = np.sort(np.argsort(readings.std(axis=0))[::-1][:4])

            # Get min and max
            self.min_vals = readings[:, self.active_axes].min(axis=0)
            self.max_vals = readings[:, self.active_axes].max(axis=0)

            readings = norm_record(t_sec=3, text="\ncenter all sticks\n")
            center = get_center(readings).reshape(1, -1)

            self.sticks = {"throttle": {}, "yaw": {}, "pitch": {}, "roll": {}}
            commands = ["up", "to the right"]
            for i, k in enumerate(self.sticks.keys()):
                readings = norm_record(t_sec=5, text="\nmove the " + k + " stick " + commands[i % 2])
                idx = np.argmax(np.abs(readings).max(axis=0))
                print("\n" + k + " axis idx: ", idx)
                self.sticks[k]["idx"] = int(idx)
                self.sticks[k]["sign_reversed"] = np.sign(readings[np.argmax(np.abs(readings[:, idx])), idx])
                readings = norm_record(t_sec=3, text="\ncenter all sticks\n")
                center = np.vstack((center, get_center(readings).reshape(1, -1)))
            print(self.sticks)
            center = center.mean(axis=0)
            for i, k in enumerate(self.sticks.keys()):
                self.sticks[k]["center"] = center[self.sticks[k]["idx"]]

            self.save_calibration(dict_to_write={
                "active_axes": self.active_axes.tolist(),
                "sticks": self.sticks,
                "min_vals": self.min_vals.tolist(),
                "max_vals": self.max_vals.tolist(),
                }, full_path=calibration_file_path)

    def save_calibration(self, dict_to_write, full_path):
        json_writer(dict_to_write, full_path)

    def load_calibration(self, path):
        json_reader(path)

    def mapFromTo(self, x, a, b, c, d):
        y = (x - a) / (b - a) * (d - c) + c
        return y

    def norm_read(self):
        self.norm_reading = np.array(self.read(with_buttons=False)["axes"])[self.active_axes]
        self.norm_reading = np.array([self.mapFromTo(r, self.min_vals[i], self.max_vals[i], -1, 1) for i, r in enumerate(self.norm_reading)])
        return self.norm_reading

    def calib_read(self):
        t0 = time()
        self.calib_reading = self.norm_read()
        for i, k in enumerate(self.sticks.keys()):
            self.calib_reading[self.sticks[k]["idx"]] *= self.sticks[k]["sign_reversed"]
            if self.calib_reading[self.sticks[k]["idx"]] <= self.sticks[k]["center"]:
                self.calib_reading[self.sticks[k]["idx"]] = self.mapFromTo(self.calib_reading[self.sticks[k]["idx"]], -1, self.sticks[k]["center"], -1, 0)
            else:
                self.calib_reading[self.sticks[k]["idx"]] = self.mapFromTo(self.calib_reading[self.sticks[k]["idx"]], self.sticks[k]["center"], 1, 0, 1)
        return self.calib_reading


def get_sticks(sticks_queue, rc):
    while True:
        sticks_queue.put_nowait([time(), rc.calib_read()])


def save_sticks(sticks_queue, path):
    # df = pd.DataFrame()
    sticks = np.empty(shape=(0, 5))
    while True:
        t, sticks = sticks_queue.get()
        sticks = np.vstack((sticks, np.append(t, rc.calib_read())))
    pickle.dump(sticks, path)


if __name__ == '__main__':

    print("start")

    rc = Joystick()
    run = rc.status
    rc.calibrate("frsky.json", load_calibration_file=True)
    while run:
        rc.calib_read()
        rc.render_axes()

    """
    run = ret
    while run:
        # time.sleep(0.1)
        if msvcrt.kbhit() and msvcrt.getch() == chr(27).encode(): # detect ESC
            run = False
    
        ret, info = joystickapi.joyGetPosEx(id)
        if ret:
            btns = [(1 << i) & info.dwButtons != 0 for i in range(caps.wNumButtons)]
            axisXYZ = [info.dwXpos-startinfo.dwXpos, info.dwYpos-startinfo.dwYpos, info.dwZpos-startinfo.dwZpos]
            axisRUV = [info.dwRpos-startinfo.dwRpos, info.dwUpos-startinfo.dwUpos, info.dwVpos-startinfo.dwVpos]
            # if info.dwButtons:
            #     print("buttons: ", btns)
            # if any([abs(v) > 10 for v in axisXYZ]):
            #     print("axis:", axisXYZ)
            # if any([abs(v) > 10 for v in axisRUV]):
            #     print("roation axis:", axisRUV)
            drawnow(make_fig)
    """
    print("end")