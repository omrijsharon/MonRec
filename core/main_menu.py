from time import sleep
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
import multiprocessing as mp
import os
from tabulate import tabulate
from winsound import PlaySound, SND_FILENAME

from functools import partial
from core.calib_menu import calib_menu
from core.config_menu import get_calib_file, get_rec_dir, stop_listener, config_menu
from core.recording import init_joystick, RecordingManager, listen2sticks
from utils.json_helper import json_reader, json_writer
from tooltip import createToolTip
from tests.tk_widget_dnd import dnd, get_widgets_position, set_widgets_position, quit_wrapper
from winfo import getWindowSizes, get_window_monitor


def main():
    def start_config_menu():
        btn_config.config(state=DISABLED)
        stop_listening()
        var_is_config_menu_open.set(True)
        config_menu(root, joystick, config, config_file_path)

    def start_calib_menu():
        btn_calib.config(state=DISABLED)
        stop_listening()
        var_is_calib_menu_open.set(True)
        calib_menu(root, joystick, config["calib_file"])

    def get_toplevel_list():
        toplevel_list = [child.title() for child in root.winfo_children() if isinstance(child, Toplevel)]
        return toplevel_list

    def start_listening():
        btn_listen.config(state=DISABLED)
        if len(sticks_listener) == 0:
            sticks_listener.append(mp.Process(target=listen2sticks, args=(config, joystick, stop_grab_event, listener_killer_event)))
            sticks_listener[0].start()
            btn_listen.config(command=stop_listening)
        else:
            messagebox.showerror("Error", "Already listening")
        btn_listen.config(text="Stop\nListening")
        btn_listen.config(state=NORMAL)

    def stop_listening():
        btn_listen.config(state=DISABLED)
        if len(sticks_listener) > 0:
            if sticks_listener[0].is_alive():
                stop_listener(sticks_listener[0], listener_killer_event)
            # else:
            #     is_alive = sticks_listener[0].is_alive()
            #     messagebox.showerror("Error", f"Num of listeners: {len(sticks_listener)}.\nListener is_alive?: {is_alive}.")
            del sticks_listener[0]
            # messagebox.showinfo("Info", "Stopped listening")
            btn_listen.config(text="Start\nListening", command=start_listening)
        btn_listen.config(state=NORMAL)

    def start_recording():
        if var_is_auto_detection.get():
            windowsize_temp = getWindowSizes()
            window_info = [win for win in windowsize_temp if not "".join(game_names).lower().find(win["name"].strip(" ").lower())==-1]
            if len(window_info) > 0:
                window_info = window_info[0]
                monitor = get_window_monitor(window_info, return_screenshot=False, is_fullscreen=var_is_fullscreen.get())
                lbl_game_detected.config(text=window_info["name"])
                lbl_game_resolution.config(text=f"Resolution {window_info['width']}x{window_info['height']}")
                config["monitor"].update(monitor)
                config.update({"game": window_info["name"]})
            else:
                messagebox.showerror("Error", "No game window found")
                return
        rec_manager.update_config(config)
        rec_manager.start_recording()
        btn_listen.config(state=DISABLED)
        lbl_recording_status.config(text="Status: Recording")
        indicator_canvas.itemconfig(oval, fill='red')
        if var_is_sound_on.get():
            PlaySound('start.wav', SND_FILENAME)

    def stop_recording():
        stop_grab_event.set()
        if var_is_sound_on.get():
            PlaySound('stop.wav', SND_FILENAME)
        indicator_canvas.itemconfig(oval, fill='#F0F0F0')
        lbl_recording_status.config(text="Status: Stopping...")
        data, headers = rec_manager.stop_recording()
        btn_listen.config(state=NORMAL)
        lbl_summary.config(text="Summary of the last recording:\n" + tabulate(data, headers=headers))
        lbl_recording_status.config(text="Status: Not recording.")

    def default_config():
        monitor = {
            "top": 0,
            "left": 0,
            "width": 1280,
            "height": 720,
            "mon": 0
        }
        config = {"rec_dir": "", "calib_file": "", "num_workers": 2, "buffer_size": 64, "type": "jpg", "compression": 70}
        config.update({"monitor": monitor})
        config.update({"Full Screen": "Windowed"})
        config.update({"camera_angle": 30})
        config.update({"game": "TrypFPV"})
        config.update({"arm_switch": "AUX1"})
        config.update({"rates": 3*[[[1.0], [0.7], [0.0]]]})
        return config

    def validate_config(config):
        dflt_config = default_config()
        for k, v in dflt_config.items():
            if k not in config:
                config[k] = v
        return config

    def save_widgets(widgets_position, path):
        pass
        # with open(path, 'w') as f:
        #     json_writer(widgets_position, f)

    def quit_app():
        if lbl_recording_status["text"] == "Status: Recording":
            if messagebox.askokcancel("Quit", "Are you sure you want to quit?\nRecording will be stopped."):
                stop_listening()
                sleep(0.5)
                stop_recording()
                root.quit()
            else:
                return

        if btn_listen["text"] == "Stop\nListening":
            if messagebox.askokcancel("Quit", "Are you sure you want to quit?\nListening will be stopped."):
                stop_listening()
                root.quit()
            else:
                return
        root.destroy()

    def Refresher():
        if stop_grab_event.is_set() and rec_manager.is_recording:
            stop_recording()
        elif not stop_grab_event.is_set() and not rec_manager.is_recording:
            start_recording()
        toplevel_list = get_toplevel_list()
        if "Calibration" not in "".join(toplevel_list) and var_is_calib_menu_open.get(): # calib menu just closed
                btn_calib.config(state=NORMAL)
                var_is_calib_menu_open.set(False)
                joystick.load_calibration(config["calib_file"])
        if "Configuration" not in "".join(toplevel_list) and var_is_config_menu_open.get(): # config menu just closed
                btn_config.config(state=NORMAL)
                var_is_config_menu_open.set(False)
                config.update(json_reader(config_file_path))

        root.after(200, Refresher)

    root = Tk()
    root.title("FPV Simulator Recording App")
    root.geometry('%dx%d+%d+%d' % (480, 480, 0, 0))
    root.resizable(False, False)
    root.attributes('-topmost', 'false')

    stop_grab_event = mp.Event()
    stop_grab_event.set()
    listener_killer_event = mp.Event()
    config_file_path = os.path.join(os.path.split(os.getcwd())[0], "config", "ui.json")
    # print(config_file_path)

    # create default config file:
    if os.path.exists(config_file_path):
        config = json_reader(config_file_path)
        config = validate_config(config)
    else:
        config = default_config()

    # Initiate joystick instance:
    config = get_calib_file(root, config)
    try:
        joystick = init_joystick(config)
    except Exception as e:
        messagebox.showerror("Error", "Could not initialize joystick.\n" + str(e))
        root.quit()

    # Initiate recording manager:
    config = get_rec_dir(root, config)
    rec_manager = RecordingManager(joystick, config, stop_grab_event)
    sticks_listener = []

    # Create ui menu:
    x0, y0 = 20, 20
    btn_x_dist = 150
    btn_width, btn_height = 10, 3
    font = ("Helvetica", 16)

    btn_listen = Button(root, text="Start\nListening", command=start_listening, width=btn_width, height=btn_height, font=font)
    btn_listen.place(x=x0, y=y0)

    btn_config = Button(root, text="Configure\nRecording", width=btn_width, height=btn_height, font=font, command=start_config_menu)
    btn_config.place(x=x0 + btn_x_dist*1, y=y0)
    var_is_config_menu_open = BooleanVar()
    var_is_config_menu_open.set(False)

    btn_calib = Button(root, text="Calibrate\nsticks", width=btn_width, height=btn_height, command=start_calib_menu, font=font)
    btn_calib.place(x=x0 + btn_x_dist*2, y=y0)
    var_is_calib_menu_open = BooleanVar()
    var_is_calib_menu_open.set(False)

    var_is_sound_on = BooleanVar()
    var_is_sound_on.set(True)
    chk_sound = Checkbutton(root, text="Sound", variable=var_is_sound_on)
    chk_sound.place(x=18, y=116)
    chk_sound.select()
    createToolTip(chk_sound, "Enable/Disable sound when recording starts/stops.")

    game_names = ["TrypFPV", "Uncrashed", "Liftoff", "Velocidrone", "DRL"]
    var_is_auto_detection = BooleanVar()
    var_is_auto_detection.set(True)
    chk_game_detection = Checkbutton(root, text="Detect game",  variable=var_is_auto_detection)
    chk_game_detection.place(x=18, y=156)
    chk_game_detection.select()
    createToolTip(chk_game_detection, "If enabled, the game will be detected automatically.")
    lbl_game_detected = Label(root, text="")
    lbl_game_detected.place(x=38, y=176)
    lbl_game_resolution = Label(root, text="")
    lbl_game_resolution.place(x=38, y=194)

    var_is_fullscreen = BooleanVar()
    var_is_fullscreen.set(True)
    chk_fullscreen = Checkbutton(root, text="Full Screen", variable=var_is_fullscreen)
    chk_fullscreen.place(x=18, y=136)
    chk_fullscreen.select()
    createToolTip(chk_fullscreen, "If enabled, the screen capture will be adjusted accordingly.")

    lbl_recording_status = Label(root, text="Status:" + " "*10 + "Not recording", font=("Helvetica", 10))
    lbl_recording_status.place(x=26, y=225)

    indicator_canvas = Canvas(root, width=60, height=60)
    indicator_canvas.place(x=200, y=118)
    oval = indicator_canvas.create_oval(2, 2, 58, 58, width=2, fill='#F0F0F0')
    indicator_canvas.itemconfig(oval, fill='#F0F0F0')

    lbl_summary = Label(root, text="Summary of the last recording:", font=("Helvetica", 10))
    lbl_summary.place(x=40, y=265)

    btn_quit = Button(root, text="X", width=2, height=1)
    quit_func = quit_wrapper(locals(), quit_app, save_widgets, path="")
    btn_quit.config(command=quit_func)
    btn_quit.place(x=460, y=0)
    Refresher()

    # root.protocol("WM_DELETE_WINDOW", partial(quit_app, variables=locals()))
    root.protocol("WM_DELETE_WINDOW", quit_func)
    # dnd(locals(), mouse_button=3)
    root.mainloop()
    # @TODO: Delete last recording using joystick switch/aux.
    # @TODO: Test with more than 1 display.
    # @TODO: add summary in start recording lbl (done but ugly)


if __name__ == '__main__':
    main()
