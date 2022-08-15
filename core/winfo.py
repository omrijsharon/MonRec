import win32con
import win32gui
import win32process
import mss
import mss.tools
import numpy as np
import matplotlib.pyplot as plt


def isRealWindow(hWnd):
    '''Return True iff given window is a real Windows application window.'''
    if not win32gui.IsWindowVisible(hWnd):
        return False
    if win32gui.GetParent(hWnd) != 0:
        return False
    hasNoOwner = win32gui.GetWindow(hWnd, win32con.GW_OWNER) == 0
    lExStyle = win32gui.GetWindowLong(hWnd, win32con.GWL_EXSTYLE)
    if (((lExStyle & win32con.WS_EX_TOOLWINDOW) == 0 and hasNoOwner)
      or ((lExStyle & win32con.WS_EX_APPWINDOW != 0) and not hasNoOwner)):
        if win32gui.GetWindowText(hWnd):
            return True
    return False


def getWindowSizes():
    '''
    Return a list of tuples (handler, (width, height)) for each real window.
    '''
    def callback(hWnd, windows):
        if not isRealWindow(hWnd):
            return
        rect = list(win32gui.GetWindowRect(hWnd))
        name = win32gui.GetWindowText(hWnd)
        ctid, cpid = win32process.GetWindowThreadProcessId(hWnd)
        rect[0] += 8
        rect[1] += 31
        rect[2] -= 8
        rect[3] -= 8
        w, h = rect[2] - rect[0], rect[3] - rect[1]
        # windows.append({"name": name, "pid": cpid, "rect": rect, "wh": (w-16, h-39)})
        if all([r>0 for r in rect]):
            windows.append({"name": name, "pid": cpid, "rect": rect, "width": w, "height": h})
    windows = []
    win32gui.EnumWindows(callback, windows)
    return windows


def get_app_window_screenshot(window_info, monitor_number=0):
    # compression = 6
    with mss.mss() as sct:
        monitor = {
            "top": window_info["rect"][1],
            "left": window_info["rect"][0],
            "width": window_info["width"],
            "height": window_info["height"],
            "mon": monitor_number,
        }
        img_byte = sct.grab(monitor)
        img = np.frombuffer(img_byte.rgb, np.uint8).reshape(monitor["height"], monitor["width"], 3)
        # plt.imshow(img)
        # plt.title(window_info["name"].strip(" ").replace(" ","_"))
        # plt.show()
        return img
