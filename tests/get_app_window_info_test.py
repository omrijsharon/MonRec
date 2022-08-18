import win32con
import win32gui
import win32process
import win32api
import psutil


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
        rect[1] += +31
        rect[2] -= 8
        rect[3] -= 8
        w, h = rect[2] - rect[0], rect[3] - rect[1]
        # windows.append({"name": name, "pid": cpid, "rect": rect, "wh": (w-16, h-39)})
        if all([r>0 for r in rect]):
            windows.append({"name": name, "pid": cpid, "rect": rect, "wh": (w, h)})
    windows = []
    win32gui.EnumWindows(callback, windows)
    return windows

if __name__ == '__main__':
    import mss
    import mss.tools
    import numpy as np
    import matplotlib.pyplot as plt

    compression = 9
    monitor_number = 0
    for win in getWindowSizes():
        print(win)
        with mss.mss() as sct:
            sct.compression_level = compression
            mon = sct.monitors[monitor_number]
            monitor = {
                "top": win["rect"][1],
                "left": win["rect"][0],
                "width": win["wh"][0],
                "height": win["wh"][1],
                "mon": monitor_number,
            }
            img_byte = sct.grab(monitor)
            img = np.frombuffer(img_byte.rgb, np.uint8).reshape(monitor["height"], monitor["width"], 3)[:, :, ::-1]
            plt.imshow(img)
            plt.title(win["name"].strip(" ").replace(" ","_"))
            plt.show()

