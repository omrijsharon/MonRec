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
from copy import deepcopy
from recording import RecordingManager, init_joystick, listen2sticks
from functools import partial
from tabulate import tabulate


def config_menu(root, config, config_file_path):

    def save_config():
        json_writer(config, config_file_path)
        if os.path.exists(config_file_path):
            messagebox.showinfo("Info", f"Configuration saved")
            on_closing()

    def on_closing():
        if not config == original_config:
            if messagebox.askyesno("Save", "Save changes?"):
                save_config()

    original_config = deepcopy(config)
    window = Toplevel()
    window.wm_transient(root)
    window.title("Recording Configuration")
    # window.geometry('%dx%d+%d+%d' % (460, 360, 0, 0))
    window.geometry('%dx%d' % (460, 360))
    window.resizable(False, False)
    # window.attributes('-topmost', 'false')

    # Rec dir
    x0, y0 = 10, 10
    var_rec_dir = StringVar()
    lbl_rec_dir = Label(window, text="Recordings directory:")
    lbl_rec_dir.place(x=x0, y=y0)
    entry_rec_dir = Entry(window, textvariable=var_rec_dir, width=64)
    entry_rec_dir.place(x=x0, y=y0+18)
    var_rec_dir.set(config.get("rec_dir"))
    var_rec_dir.trace("w", lambda name, index, mode, sv=var_rec_dir: config.update({"rec_dir": sv.get()}))
    btn_rec_dir = Button(window, text="Browse", command=partial(lambda x: x.set(os.path.join(filedialog.askdirectory(initialdir=var_rec_dir.get(), title="Select a directory to save the recordings"), config["game"])), var_rec_dir))
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
    x0, y0 = 10, 112
    lbl_resolution = Label(window, text="Resolution:")
    lbl_resolution.place(x=x0, y=y0)
    var_width = StringVar()
    var_height = StringVar()
    lbl_width = Label(window, text="Width:")
    lbl_width.place(x=x0+10, y=y0+18)
    entry_width = Entry(window, textvariable=var_width, width=5)
    entry_width.place(x=x0+13, y=y0+36)
    var_width.set(str(config.get("resolution").get("width")))
    var_width.trace("w", lambda name, index, mode, sv=var_width: config.update({"resolution": {"width": int(sv.get())}}))
    lbl_height = Label(window, text="Height:")
    lbl_height.place(x=x0+80, y=y0+18)
    Label(window, text="X").place(x=x0+56, y=y0+36)
    entry_height = Entry(window, textvariable=var_height, width=5)
    entry_height.place(x=x0+83, y=y0+36)
    var_height.set(str(config.get("resolution").get("height")))
    var_height.trace("w", lambda name, index, mode, sv=var_height: config.update({"resolution": {"height": int(sv.get())}}))

    # Workers
    x0, y0 = 10, 250
    var_num_workers = StringVar()
    lbl_num_workers = Label(window, text="# workers:")
    lbl_num_workers.place(x=x0, y=y0)
    entry_num_workers = Entry(window, textvariable=var_num_workers, width=5)
    entry_num_workers.place(x=x0+13, y=y0+18)
    var_num_workers.set(config.get("num_workers"))
    var_num_workers.trace("w", lambda name, index, mode, sv=var_num_workers: config.update({"num_workers": int(sv.get())}))

    # Buffer size
    x0, y0 = 80, 250
    var_buffer_size = StringVar()
    lbl_buffer_size = Label(window, text="Buffer size:")
    lbl_buffer_size.place(x=x0, y=y0)
    entry_buffer_size = Entry(window, textvariable=var_buffer_size, width=5)
    entry_buffer_size.place(x=x0+13, y=y0+18)
    var_buffer_size.set(config.get("buffer_size"))
    var_buffer_size.trace("w", lambda name, index, mode, sv=var_buffer_size: config.update({"buffer_size": int(sv.get())}))

    # Type
    x0, y0 = 10, 184
    var_type = StringVar()
    var_type.set(config.get("type"))
    lbl_type = Label(window, text="Image type:")
    lbl_type.place(x=x0, y=y0)
    option_menu_type = OptionMenu(window, var_type, "jpg", "png")
    option_menu_type.place(x=x0+3, y=y0+18)
    var_type.trace("w", lambda name, index, mode, sv=var_type: config.update({"type": sv.get()}))

    # compression
    x0, y0 = 80, 184
    var_compression = StringVar()
    lbl_compression = Label(window, text="Compression:")
    lbl_compression.place(x=x0, y=y0)
    entry_compression = Entry(window, textvariable=var_compression, width=5)
    entry_compression.place(x=x0+13, y=y0+18)
    var_compression.set(config.get("compression"))
    var_compression.trace("w", lambda name, index, mode, sv=var_compression: config.update({"compression": int(sv.get())}))

    # Rates Table
    x0, y0 = 204, 112
    rates(window, config, x0, y0)

    # Game
    x0, y0 = 204, 220
    var_game = StringVar()
    var_game.set(config.get("game"))
    lbl_game = Label(window, text="Game:")
    lbl_game.place(x=x0, y=y0)
    option_menu_game = OptionMenu(window, var_game, "TrypFPV", "Uncrashed", "Liftoff", "Velocidrone", "DRL")
    option_menu_game.place(x=x0 + 3, y=y0 + 18)
    var_game.trace("w", lambda name, index, mode, sv=var_game: config.update({"game": sv.get()}))

    # save
    x0, y0 = 20, 296
    btn_save = Button(window, text="Save", width=60, height=3, command=save_config)
    btn_save.place(x=x0, y=y0)

    root.protocol("WM_DELETE_WINDOW", on_closing)
    window.mainloop()



def rates(window, config, x0, y0):
    def set_list_idx_inplace(value, l, i, j):
        l[i][j][0] *= 0
        l[i][j][0] += value
    lbl_rates = Label(window, text="Betaflight Rates:")
    lbl_rates.place(x=x0, y=y0)
    axis = ["Roll", "Pitch", "Yaw"]
    rate_names = ["RC Rate", "Rate", "RC Expo"]
    lbl_axis = [Label(window, text=axis[i]) for i in range(len(axis))]
    [lbl_axis[i].place(x=x0, y=y0+40+i*20) for i in range(len(axis))]
    lbl_rate_names = [Label(window, text=rate_names[i]) for i in range(len(rate_names))]
    [lbl_rate_names[i].place(x=x0+40+i*50, y=20+y0) for i in range(len(lbl_rate_names))]
    var_rates = 3 * [3 * [StringVar()]]
    ent_rates = 3 * [3 * [Entry(window, width=5)]]
    for i in range(len(axis)):
        for j in range(len(rate_names)):
            var_rates[i][j] = StringVar()
            var_rates[i][j].set(config["rates"][i][j])
            ent_rates[i][j] = Entry(window, textvariable=var_rates[i][j], width=7)
            ent_rates[i][j].place(x=x0+43+j*50, y=y0+40+i*20)
            var_rates[i][j].trace("w", lambda name, index, mode, sv=var_rates[i][j], k=i, l=j: set_list_idx_inplace(float(sv.get()), config["rates"], k, l))
            # var_rates[i][j].set(config.get("rates").get(axis[i]).get(rate_names[j]))


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
