import os
import numpy as np
from time import sleep
from functools import partial
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
from get_sticks import Joystick
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg')

from utils.json_helper import json_reader, json_writer


def calib_menu(root, joystick: Joystick, calib_file_path=None):
    if calib_file_path == "":
        calib_file_path = None

    def get_calib_file_path(calib_file_path=None):
        if calib_file_path is None:
            calib_file_path = filedialog.askdirectory(initialdir=os.getcwd(),
                                                      title="Select a directory to save the calibration file")
            calib_file_path = os.path.join(calib_file_path, "calibration.json")
            return calib_file_path
        else:
            if not os.path.exists(calib_file_path):
                ans = messagebox.askquestion("Warning", "The selected file does not exist.\n If you wish to create it choose yes.\n If you wish to find it, choose no.", icon="warning")
                if ans == "yes":
                    return get_calib_file_path()
                else:
                    calib_file_path = filedialog.askopenfilename(filetypes=[("Calibration files (*.json)", ".json")], title="Select a calibration file")
                    return get_calib_file_path(calib_file_path=calib_file_path)
            else:
                return calib_file_path

    def plot_raw_sticks(readings):
        ax_raw_sticks.clear()
        ax_raw_sticks.bar(stick_axes, readings, align="center", width=0.9)
        ax_raw_sticks.axes.set_xlim(-0.5, 5.5)
        [ax_raw_sticks.text(i*1, read, read, ha='center', va='bottom', fontsize=10) for i, read in enumerate(readings)]
        ax_raw_sticks.set_ylim([0, 65535])
        ax_raw_sticks.yaxis.set_major_locator(plt.NullLocator())
        ax_raw_sticks.xaxis.set_major_locator(plt.NullLocator())
        # ax.set_title("Sticks raw readings")
        canvas_raw_sticks.draw()

    def get_map_dict():
        return {name.get(): idx for idx, name in enumerate(var_sticks)}

    def norm_stick(readings, idx):
        invert = -2 * var_invert[idx].get() + 1
        scale = vars_max[idx].get() - vars_min[idx].get()
        if scale == 0:
            scale = 1
        zero2one = (readings[idx] - vars_min[idx].get()) / scale
        return (zero2one * 2 - 1) * invert

    def norm_map(readings):
        map_dict = get_map_dict()
        return {axis_name: norm_stick(readings, map_dict[axis_name]) for (i, axis_name) in enumerate(stick_names)}

    def calib_map(readings):
        norm_readings = norm_map(readings)
        for i, k in enumerate(norm_readings.keys()):
            if "AUX" not in k:
                if norm_readings[k] <= var_center_sticks[k].get():
                    norm_readings[k] = joystick.mapFromTo(norm_readings[k], -1, var_center_sticks[k].get(), -1, 0)
                else:
                    norm_readings[k] = joystick.mapFromTo(norm_readings[k], var_center_sticks[k].get(), 1, 0, 1)
        return norm_readings

    def plot_mapped_sticks(readings):
        alpha = 0.2
        if var_is_center.get():
            calib_readings = calib_map(readings)
        else:
            calib_readings = norm_map(readings)
        for i, (x_axis_name, y_axis_name) in enumerate([["Yaw", "Throttle"],["Roll", "Pitch"]]):
            ax_mapped_sticks[i].clear()
            ax_mapped_sticks[i].plot([-1, 1], [0, 0], 'b', lw=3, alpha=alpha)
            ax_mapped_sticks[i].plot([0, 0], [-1, 1], 'b', lw=3, alpha=alpha)
            ax_mapped_sticks[i].scatter(calib_readings[x_axis_name], calib_readings[y_axis_name], s=100, c="r", alpha=alpha)
            ax_mapped_sticks[i].axis("square")
            ax_mapped_sticks[i].yaxis.set_major_locator(plt.NullLocator())
            ax_mapped_sticks[i].xaxis.set_major_locator(plt.NullLocator())
            ax_mapped_sticks[i].set_xlim([-1, 1])
            ax_mapped_sticks[i].set_ylim([-1, 1])
        canvas_mapped_sticks.draw()

    def get_map_idx():
        return [var_stick.get() for i, var_stick in enumerate(var_sticks)]

    def set_last_stick(var_stick):
        last_stick.set(var_stick.get())

    def axes_swap(idx, cmb_stick, vevent):
        current_stick.set(cmb_stick.get())
        if current_stick.get() != last_stick.get():
            for i, var_stick in enumerate(var_sticks):
                if var_stick.get() == current_stick.get() and i != idx:
                    var_stick.set(last_stick.get())
                    break

    def check_minmax(readings):
        vals_min = np.array([var_min.get() for var_min in vars_min])
        vals_max = np.array([var_max.get() for var_max in vars_max])
        min_idx = np.argwhere(readings < vals_min)
        max_idx = np.argwhere(readings > vals_max)
        if len(min_idx) > 0:
            for i in min_idx:
                vars_min[i.item()].set(readings[i.item()])
        if len(max_idx) > 0:
            for i in max_idx:
                vars_max[i.item()].set(readings[i.item()])
        # print(vals_min, vals_max)

    def center_sticks():
        readings = joystick.read()
        for _ in range(30):
            readings = np.vstack((readings, joystick.read()))
            sleep(1e-6)
        readings = readings[1:]
        readings = np.mean(readings, axis=0)
        calib_readings = norm_map(readings)
        for k, v in var_center_sticks.items():
            v.set(calib_readings[k])
        var_is_center.set(True)

    def save_calib():
        valid_list = [var_min.get() < var_max.get() for var_min, var_max in zip(vars_min, vars_max)]
        if all(valid_list) and var_is_center.get():
            sticks = {
                name.get():
                    {
                        "idx": idx,
                        "center": var_center_sticks[name.get()].get()
                    }
                for idx, name in enumerate(var_sticks)
                if "AUX" not in name.get()
            }
            switches = {name.get(): {"idx": idx} for idx, name in enumerate(var_sticks) if "AUX" in name.get()}
            vals_min = [var_min.get() for var_min in vars_min]
            vals_max = [var_max.get() for var_max in vars_max]
            invert = [-2 * vinvert.get() + 1 for vinvert in var_invert]
            dict_to_write = {
                "sticks": sticks,
                "switches": switches,
                "min_vals": vals_min,
                "max_vals": vals_max,
                "sign_reverse": invert
            }
            joystick.save_calibration(dict_to_write=dict_to_write, full_path=var_calib_file.get())
            joystick.update(**dict_to_write)
            var_is_saved.set(True)
            messagebox.showinfo("Calibration saved", "Calibration saved to {}".format(var_calib_file.get()), icon="info")
        else:
            invalid_names_str = ",".join([name.get() for idx, name in enumerate(var_sticks) if not valid_list[idx]])
            if not var_is_center.get():
                center_error_str = "Sticks were not centered."
            else:
                center_error_str = ""
            messagebox.showerror("Invalid calibration", f"Please move {invalid_names_str} all the way before saving.\n{center_error_str}", icon="error")

    def load_calib_to_ui(with_ui=False):
        if with_ui:
            calib_file = filedialog.askopenfilename(filetypes=[("Calibration files (*.json)", ".json")], title="Select a calibration file")
            if not os.path.exists(calib_file):
                messagebox.showerror("File not found", f"Calibration file {calib_file} not found", icon="error")
                load_calib_to_ui(with_ui=True)
            else:
                window.title("Recording Configuration - {}".format(os.path.split(calib_file)[-1]))
        else:
            calib_file = var_calib_file.get()
        if not joystick.calib:
            joystick.load_calibration(calibration_file_path=calib_file)
        #min-max
        [var_min.set(int(joystick_min_val)) for joystick_min_val, var_min in zip(joystick.min_vals, vars_min)]
        [var_max.set(int(joystick_max_val)) for joystick_max_val, var_max in zip(joystick.max_vals, vars_max)]
        #invert
        [var_inv.set(int((-joystick_inv+1)/2)) for joystick_inv, var_inv in zip(joystick.sign_reverse, var_invert)]
        #names
        [var_sticks[v["idx"]].set(k) for k, v in joystick.sticks.items()]
        [var_sticks[v["idx"]].set(k) for k, v in joystick.switches.items()]
        #center
        [var_center_sticks[k].set(v["center"]) for k, v in joystick.sticks.items()]
        var_is_center.set(True)
        # saved
        var_is_saved.set(False)

    def reset_calib():
        [var_stick.set(stick_names[i]) for i, var_stick in enumerate(var_sticks)]
        [var_invert[i].set(0) for i in range(n_sticks)]
        readings = joystick.read()[0]
        [var_min.set(readings[i]) for i, var_min in enumerate(vars_min)]
        [var_max.set(readings[i]) for i, var_max in enumerate(vars_max)]
        var_is_saved.set(False)
        var_is_center.set(False)

    def Refresher():
        readings = joystick.read()[0]
        plot_raw_sticks(readings)
        plot_mapped_sticks(readings)
        check_minmax(readings)
        window.after(50, Refresher)

    window = Toplevel()
    window.wm_transient(root)
    window.title("Recording Configuration")
    # window.geometry('%dx%d+%d+%d' % (460, 360, 0, 0))
    window.geometry('%dx%d' % (430, 500))
    window.resizable(False, False)
    # window.attributes('-topmost', 'false')

    # Plot raw sticks
    stick_axes = ['X', 'Y', 'Z', 'R', 'U', 'V']
    stick_names = ["Throttle", "Roll", "Pitch", "Yaw", "AUX1", "AUX2"]
    fig_raw_sticks = Figure(figsize=(4.7, 2))
    fig_raw_sticks.patch.set_facecolor('#F0F0F0')
    ax_raw_sticks = fig_raw_sticks.add_subplot(111)
    canvas_raw_sticks = FigureCanvasTkAgg(fig_raw_sticks, master=window)
    canvas_raw_sticks.get_tk_widget().place(x=-30, y=56)

    # Plot mapped sticks
    fig_mapped_sticks = Figure(figsize=(4.7, 2))
    fig_mapped_sticks.patch.set_facecolor('#F0F0F0')
    ax_mapped_sticks = []
    ax_mapped_sticks.append(fig_mapped_sticks.add_subplot(121))
    ax_mapped_sticks.append(fig_mapped_sticks.add_subplot(122))
    canvas_mapped_sticks = FigureCanvasTkAgg(fig_mapped_sticks, master=window)
    canvas_mapped_sticks.get_tk_widget().place(x=-30, y=266)

    # Calibration file path
    calib_file_path = get_calib_file_path(calib_file_path)
    var_calib_file = StringVar()
    var_calib_file.set(calib_file_path)
    lbl_calib_file = Label(window, text="Sticks calibration file:")
    lbl_calib_file.place(x=20, y=20)
    entry_calib_file = Entry(window, textvariable=var_calib_file, width=52)
    entry_calib_file.place(x=26, y=40)
    btn_calib_file = Button(window, text="Browse", command=lambda: var_calib_file.set(filedialog.askopenfilename(filetypes=[("Calibration files (*.json)", ".json")], title="Select a calibration file")))
    btn_calib_file.place(x=344, y=37)

    # axes mapping
    n_sticks = len(stick_axes)
    last_stick = StringVar()
    current_stick = StringVar()
    var_sticks = [StringVar() for _ in range(n_sticks)]
    [var_stick.set(stick_names[i]) for i, var_stick in enumerate(var_sticks)]
    cmb_sticks = [ttk.Combobox(window, textvariable=var_stick, values=stick_names, postcommand=partial(set_last_stick, var_stick), state="readonly", width=6) for var_stick in var_sticks]
    [cmb_stick.bind("<<ComboboxSelected>>", partial(axes_swap, idx, cmb_stick)) for idx, cmb_stick in enumerate(cmb_sticks)]
    [cmb_stick.place(x=29 + i*61, y=236) for i, cmb_stick in enumerate(cmb_sticks)]

    # axes inversion checkboxes
    var_invert = [IntVar() for _ in range(n_sticks)]
    [var_invert[i].set(0) for i in range(n_sticks)]
    chk_invert = [Checkbutton(window, text="Invert", variable=var_invert[i]) for i in range(n_sticks)]
    [chk_invert[i].place(x=29 + i*61, y=262) for i in range(n_sticks)]

    # axes min/max values
    readings = joystick.read()[0]
    vars_min = [IntVar(value=readings[i]) for i in range(n_sticks)]
    vars_max = [IntVar(value=readings[i]) for i in range(n_sticks)]

    # Reset Calibration
    btn_reset = Button(window, text="Reset", command=reset_calib, width=10)
    btn_reset.place(x=29, y=460)

    # Center sticks
    var_is_center = BooleanVar()
    var_is_center.set(False)
    var_center_sticks = {stick_name: DoubleVar() for stick_name in stick_names[:-2]}
    btn_center_sticks = Button(window, text="Center sticks", command=partial(center_sticks), width=10)
    btn_center_sticks.place(x=148, y=460)

    # load button
    btn_load = Button(window, text="Load", command=partial(load_calib_to_ui, True), width=10)
    btn_load.place(x=228, y=460)

    # save button
    var_is_saved = BooleanVar()
    var_is_saved.set(False)
    btn_save = Button(window, text="Save", command=save_calib, width=10)
    btn_save.place(x=308, y=460)

    if os.path.exists(var_calib_file.get()):
        load_calib_to_ui()

    Refresher()
    window.mainloop()


if __name__ == '__main__':
    pass
