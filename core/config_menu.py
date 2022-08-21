import os

from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog

import numpy as np

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
from PIL.ImageTk import PhotoImage
from PIL import Image
from recording import stop_func
from winfo import getWindowSizes, get_window_monitor
from tests.tk_widget_dnd import dnd, get_widgets_position, set_widgets_position, quit_wrapper


def config_menu(root, joystick, config, config_file_path):

    def save_config():
        json_writer(config, config_file_path)
        if os.path.exists(config_file_path):
            messagebox.showinfo("Info", f"Configuration saved")
            window.destroy()
        else:
            messagebox.showerror("Error", "Could not save configuration file. Check permissions")

    def on_closing():
        if not config == original_config:
            if var_num_capture_workers.get() == 0:
                messagebox.showerror("Error", "Number of capture workers must be greater than 0")
                return
            if var_num_save_workers.get() == 0:
                messagebox.showerror("Error", "Number of save workers must be greater than 0")
                return
            if var_num_save_workers.get() <= var_num_capture_workers.get():
                messagebox.showwarning("Warning", "Number of save workers is less than number of capture workers.\n"
                                                  "This may cause problems with the recording.\n"
                                                  "Consider increasing the number of save workers.")
            if messagebox.askyesno("Save", "Save changes?"):
                save_config()
        window.destroy()

    def change_resolution(e=None):
        windowsize_temp = getWindowSizes()
        window_info = [win for win in windowsize_temp if win["name"] == var_game.get()][0]
        monitor, img[0] = get_window_monitor(window_info, return_screenshot=True, is_fullscreen=var_fullscreen.get() == "Full Screen")
        config["monitor"].update(monitor)
        config.update({"game": window_info["name"]})
        var_width.set(config["monitor"]["width"])
        var_height.set(config["monitor"]["height"])
        scale_inv = img[0].shape[0] / max_height
        h = img[0].shape[0] // scale_inv
        w = img[0].shape[1] // scale_inv
        if h > max_height or w > max_width:
            scale_inv = img[0].shape[1] / max_width
            h = img[0].shape[0] // scale_inv
            w = img[0].shape[1] // scale_inv
        img[0] = PhotoImage(Image.fromarray(img[0]).resize((int(w), int(h)), Image.ANTIALIAS))
        canvas.create_image(20, 20, anchor="nw", image=img[0])

    def Refresher():
        readings = joystick.calib_read()
        if window.winfo_exists():
            if stop_func(calib_readings=readings, calib_dict=calib_dict, switch=var_arm_switch.get(), stop_value=stop_value):
                indicator_canvas.itemconfig(oval, fill='#F0F0F0')
            else:
                indicator_canvas.itemconfig(oval, fill='red')
        window.after(200, Refresher)

    original_config = deepcopy(config)
    window = Toplevel()
    window.wm_transient(root)
    window.title("Recording Configuration")
    # window.geometry('%dx%d+%d+%d' % (460, 360, 0, 0))
    window.geometry('%dx%d' % (460, 560))
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

    # Workers
    x0, y0 = 44, 115
    var_num_save_workers = StringVar()
    var_num_capture_workers = StringVar()
    lbl_num_workers = Label(window, text="# workers:")
    lbl_num_workers.place(x=x0, y=y0-20)
    lbl_num_save_workers = Label(window, text="Saving:")
    lbl_num_save_workers.place(x=82, y=y0)
    lbl_num_capture_workers = Label(window, text="Capturing:")
    lbl_num_capture_workers.place(x=10, y=y0)
    entry_num_save_workers = Entry(window, textvariable=var_num_save_workers, width=5)
    entry_num_save_workers.place(x=25, y=y0 + 20)
    entry_num_capture_workers = Entry(window, textvariable=var_num_capture_workers, width=5)
    entry_num_capture_workers.place(x=85, y=y0 + 20)
    var_num_save_workers.set(config.get("num_saving_workers"))
    var_num_save_workers.trace("w", lambda name, index, mode, sv=var_num_save_workers: config.update({"num_saving_workers": int(sv.get())}))
    var_num_capture_workers.set(config.get("num_capturing_workers"))
    var_num_capture_workers.trace("w", lambda name, index, mode, sv=var_num_capture_workers: config.update({"num_capturing_workers": int(sv.get())}))

    # Buffer size
    x0, y0 = 134, 115
    var_buffer_size = StringVar()
    lbl_buffer_size = Label(window, text="Buffer size:")
    lbl_buffer_size.place(x=x0, y=y0)
    entry_buffer_size = Entry(window, textvariable=var_buffer_size, width=5)
    entry_buffer_size.place(x=x0+13, y=y0+18)
    var_buffer_size.set(config.get("buffer_size"))
    var_buffer_size.trace("w", lambda name, index, mode, sv=var_buffer_size: config.update({"buffer_size": int(sv.get())}))

    # Arm/Rec switch
    x0, y0 = 10,  156
    var_arm_switch = StringVar()
    var_arm_switch.set(config.get("arm_switch"))
    lbl_arm_switch = Label(window, text="Arm/Rec switch:")
    lbl_arm_switch.place(x=x0, y=y0)
    cmb_arm_switch = ttk.Combobox(window, textvariable=var_arm_switch, width=6, values=["AUX1", "AUX2"], state="readonly")
    cmb_arm_switch.place(x=x0+13, y=y0+18)
    var_arm_switch.trace("w", lambda name, index, mode, sv=var_arm_switch: config.update({"arm_switch": sv.get()}))
    indicator_canvas = Canvas(window, width=30, height=30)
    indicator_canvas.place(x=x0+93, y=y0+8)
    oval = indicator_canvas.create_oval(2, 2, 27, 27, width=1, fill='#F0F0F0')
    indicator_canvas.itemconfig(oval, fill='#F0F0F0')
    #initiate sticks
    calib_dict = json_reader(config.get("calib_file"))
    stop_value = -1.0

    # Type
    x0, y0 = 10, 204
    var_type = StringVar()
    var_type.set(config.get("type"))
    lbl_type = Label(window, text="Image type:")
    lbl_type.place(x=x0, y=y0)
    cmb_type = ttk.Combobox(window, textvariable=var_type, width=5, values=["png", "jpg"], state="readonly")
    cmb_type.place(x=x0+13, y=y0+18)
    var_type.trace("w", lambda name, index, mode, sv=var_type: config.update({"type": sv.get()}))

    # compression
    x0, y0 = 80, 204
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

    # Game/Window
    x0, y0 = 10, 254
    var_game = StringVar()
    lbl_game = Label(window, text="Window:")
    lbl_game.place(x=x0, y=y0)
    windowsize = getWindowSizes()
    # game_names = ["TrypFPV", "Uncrashed", "Liftoff", "Velocidrone", "DRL"]
    win_names = [win["name"] for win in windowsize]
    var_game.set(config.get("game") if config["game"] in win_names else win_names[0])
    cmb_game = ttk.Combobox(window, textvariable=var_game, width=26, values=win_names, state="readonly")
    cmb_game.bind("<<ComboboxSelected>>", change_resolution)
    cmb_game.place(x=x0+13, y=y0+18)
    var_game.trace("w", lambda name, index, mode, sv=var_game: config.update({"game": sv.get()}))
    max_height = 250
    max_width = 440
    canvas = Canvas(window, width=max_width, height=max_height)
    canvas.place(x=x0-10, y=y0+40)
    img = [0]

    # Camera angle
    x0, y0 = 204, 212
    var_camera_angle = StringVar()
    lbl_camera_angle = Label(window, text="Camera angle:             °")
    lbl_camera_angle.place(x=x0, y=y0)
    entry_camera_angle = Entry(window, textvariable=var_camera_angle, width=3)
    entry_camera_angle.place(x=x0+93, y=y0+3)
    var_camera_angle.set(config.get("camera_angle"))
    var_camera_angle.trace("w", lambda name, index, mode, sv=var_camera_angle: config.update({"camera_angle": int(sv.get())}))

    # Resolution
    x0, y0 = 254, 233
    lbl_resolution = Label(window, text="Resolution:")
    lbl_resolution.place(x=x0-50, y=y0+15)
    var_width = StringVar()
    var_height = StringVar()
    lbl_width = Label(window, text="Width:")
    lbl_width.place(x=x0 + 20, y=y0)
    entry_width = Entry(window, textvariable=var_width, width=5, state="readonly")
    entry_width.place(x=x0 + 23, y=y0 + 18)
    var_width.set(str(config.get("monitor").get("width")))
    # var_width.trace("w", lambda name, index, mode, sv=var_width: config.update({"monitor": {"width": int(sv.get())}}))
    lbl_height = Label(window, text="Height:")
    lbl_height.place(x=x0 + 80, y=y0)
    Label(window, text="X").place(x=x0 + 66, y=y0 + 18)
    entry_height = Entry(window, textvariable=var_height, width=5, state="readonly")
    entry_height.place(x=x0 + 83, y=y0 + 18)
    var_height.set(str(config.get("monitor").get("height")))
    # var_height.trace("w", lambda name, index, mode, sv=var_height: config.update({"monitor": {"height": int(sv.get())}}))

    # Full screen
    x0, y0 = 204, 254
    var_fullscreen = StringVar()
    var_fullscreen.set(config.get("Full Screen"))
    cmb_fullscreen = ttk.Combobox(window, textvariable=var_fullscreen, width=12, values=["Full Screen", "Windowed"], state="readonly")
    cmb_fullscreen.place(x=x0 + 15, y=y0+18)
    var_fullscreen.trace("w", lambda name, index, mode, sv=var_fullscreen: config.update({"Full Screen": sv.get()}))
    cmb_fullscreen.bind("<<ComboboxSelected>>", change_resolution)

    # save
    x0, y0 = 366, y0+32
    btn_save = Button(window, text="Save", width=10, command=save_config)
    btn_save.place(x=x0, y=y0)

    change_resolution()
    Refresher()
    # quit_func = quit_wrapper(locals(), on_closing, verbose=True)
    window.protocol("WM_DELETE_WINDOW", on_closing)
    # dnd(locals(), mouse_button=3)
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
