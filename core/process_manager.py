import os

from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog

import multiprocessing as mp
from grab_to_queues import grab_frames_to_queue, grab_sticks_to_queue
from save_from_queues import save_frames_from_queue, save_sticks_from_queue
from time import sleep
from datetime import datetime
from functools import partial
from utils.json_helper import json_reader, json_writer
from utils.record_summary import full_summary
from get_sticks import Joystick

from recording import RecordingManager, init_joystick, listen2sticks
from functools import partial



def main():
    def start_recording():
        rec_manager.update_config(config)
        rec_manager.start_recording()
        lbl_recording_status.config(text="Recording")

    def stop_recording():
        lbl_recording_status.config(text="Stopping record...")
        rec_manager.stop_recording()
        lbl_recording_status.config(text="Not recording")

    def Refresher():
        if stop_grab_event.is_set() and rec_manager.is_recording:
            stop_recording()
        elif not stop_grab_event.is_set() and not rec_manager.is_recording:
            start_recording()
        window.after(200, Refresher)

    window = Tk()
    window.title("FPV Simulator Recording App")
    window.geometry('%dx%d+%d+%d' % (480, 280, 0, 0))
    window.resizable(False, False)
    window.attributes('-topmost', 'false')

    stop_grab_event = mp.Event()
    stop_grab_event.set()
    listener_killer_event = mp.Event()
    config_file_path = os.path.join(os.path.split(os.getcwd())[0], "config", "ui.json")
    print(config_file_path)
    if os.path.exists(config_file_path):
        config = json_reader(config_file_path)
    else:
        config = {"rec_dir": "", "calib_file": "", "resolution": {"width": 1280, "height": 720}, "num_workers": 2, "buffer_size": 64, "type": "jpg", "compression": 70}

    config = get_calib_file(window, config)
    joystick = init_joystick(config)
    config = get_rec_dir(window, config)
    rec_manager = RecordingManager(joystick, config, stop_grab_event)
    sticks_listener = mp.Process(target=listen2sticks, args=(config, joystick, stop_grab_event, listener_killer_event))
    sticks_listener.start()

    # Rec dir
    x0, y0 = 10, 10
    var_rec_dir = StringVar()
    lbl_rec_dir = Label(window, text="Recordings directory:")
    lbl_rec_dir.place(x=x0, y=y0)
    entry_rec_dir = Entry(window, textvariable=var_rec_dir, width=64)
    entry_rec_dir.place(x=x0, y=y0+18)
    var_rec_dir.set(config.get("rec_dir"))
    var_rec_dir.trace("w", lambda name, index, mode, sv=var_rec_dir: config.update({"rec_dir": sv.get()}))
    btn_rec_dir = Button(window, text="Browse", command=partial(lambda x: x.set(os.path.join(filedialog.askdirectory(initialdir=var_rec_dir.get(), title="Select a directory to save the recordings"), "trypfpv")), var_rec_dir))
    btn_rec_dir.place(x=x0 + 390, y=y0+14)

    # Calib file
    x0, y0 = 10, 56
    var_calib_file = StringVar()
    lbl_calib_file = Label(window, text="Sticks calibration file:")
    lbl_calib_file.place(x=x0, y=y0)
    entry_calib_file = Entry(window, textvariable=var_calib_file, width=64)
    entry_calib_file.place(x=x0, y=y0+18)
    var_calib_file.set(config.get("calib_file"))
    var_calib_file.trace("w", lambda name, index, mode, sv=var_calib_file: config.update({"calib_file": sv.get()}))
    btn_calib_file = Button(window, text="Browse", command=partial(lambda x: x.set(filedialog.askopenfilename(filetypes=[("Calibration files (*.json)", ".json")], title="Select a calibration file")), var_calib_file))
    btn_calib_file.place(x=x0 + 390, y=y0+14)

    # Resolution
    x0, y0 = 10, 102
    var_width = StringVar()
    var_height = StringVar()
    lbl_width = Label(window, text="Width:")
    lbl_width.place(x=x0, y=y0)
    entry_width = Entry(window, textvariable=var_width, width=5)
    entry_width.place(x=x0+3, y=y0+18)
    var_width.set(str(config.get("resolution").get("width")))
    var_width.trace("w", lambda name, index, mode, sv=var_width: config.update({"resolution": {"width": int(sv.get())}}))
    lbl_height = Label(window, text="Height:")
    lbl_height.place(x=x0+60, y=y0)
    Label(window, text="X").place(x=x0+42, y=y0+18)
    entry_height = Entry(window, textvariable=var_height, width=5)
    entry_height.place(x=x0+63, y=y0+18)
    var_height.set(str(config.get("resolution").get("height")))
    var_height.trace("w", lambda name, index, mode, sv=var_height: config.update({"resolution": {"height": int(sv.get())}}))

    # Workers
    x0, y0 = 134, 102
    var_num_workers = StringVar()
    lbl_num_workers = Label(window, text="# workers:")
    lbl_num_workers.place(x=x0, y=y0)
    entry_num_workers = Entry(window, textvariable=var_num_workers, width=5)
    entry_num_workers.place(x=x0+13, y=y0+18)
    var_num_workers.set(config.get("num_workers"))
    var_num_workers.trace("w", lambda name, index, mode, sv=var_num_workers: config.update({"num_workers": int(sv.get())}))

    # Buffer size
    x0, y0 = 205, 102
    var_buffer_size = StringVar()
    lbl_buffer_size = Label(window, text="Buffer size:")
    lbl_buffer_size.place(x=x0, y=y0)
    entry_buffer_size = Entry(window, textvariable=var_buffer_size, width=5)
    entry_buffer_size.place(x=x0+13, y=y0+18)
    var_buffer_size.set(config.get("buffer_size"))
    var_buffer_size.trace("w", lambda name, index, mode, sv=var_buffer_size: config.update({"buffer_size": int(sv.get())}))

    # Type
    x0, y0 = 10, 148
    var_type = StringVar()
    var_type.set(config.get("type"))
    lbl_type = Label(window, text="Image type:")
    lbl_type.place(x=x0, y=y0)
    option_menu_type = OptionMenu(window, var_type, "jpg", "png")
    option_menu_type.place(x=x0+3, y=y0+18)
    var_type.trace("w", lambda name, index, mode, sv=var_type: config.update({"type": sv.get()}))

    # compression
    x0, y0 = 80, 148
    var_compression = StringVar()
    lbl_compression = Label(window, text="Compression:")
    lbl_compression.place(x=x0, y=y0)
    entry_compression = Entry(window, textvariable=var_compression, width=5)
    entry_compression.place(x=x0+13, y=y0+18)
    var_compression.set(config.get("compression"))
    var_compression.trace("w", lambda name, index, mode, sv=var_compression: config.update({"compression": int(sv.get())}))

    # save
    x0, y0 = 300, 110
    btn_save = Button(window, text="Save", width=20, height=5, command=lambda: json_writer(config, config_file_path))
    btn_save.place(x=x0, y=y0)

    # Start Recording
    x0, y0 = 12, 220
    lbl_recording_status = Label(window, text="Recording status: Not recording", font=(None, 16))
    # btn_start_recording = Button(window, text="Start Recording", width=61, height=3)
    # btn_start_recording.config(command=rec_manager.start_recording)
    lbl_recording_status.place(x=x0, y=y0)

    Refresher()
    window.mainloop()
    stop_listener(sticks_listener, listener_killer_event)
    #@TODO: add calibration window
    #@TODO: add summary in start recording lbl
    #@TODO: add rates to config file

def stop_listener(sticks_listener, listener_killer_event):
    listener_killer_event.set()
    sleep(0.5)
    if sticks_listener.is_alive():
        sticks_listener.terminate()
    sticks_listener.join()


def get_calib_file(window, config):
    counter = 0
    while os.path.exists(config.get("calib_file")) is False:
        config["calib_file"] = filedialog.askopenfilename(filetypes=[("Calibration files (*.json)", ".json")],
                                                          initialdir=os.getcwd())
        counter += 1
        if counter > 3:
            messagebox.showerror("Error", "Calibration file not found")
            window.destroy()
            break
    return config


def get_rec_dir(window, config):
    counter = 0
    while os.path.exists(config.get("rec_dir")) is False:
        config["rec_dir"] = filedialog.askdirectory(initialdir=os.path.expanduser("~"),
                                                    title="Select a directory to save the recordings")
        counter += 1
        if counter > 3:
            messagebox.showerror("Error", "Recording directory not selected")
            window.destroy()
            break
    return config

if __name__ == '__main__':
    main()
