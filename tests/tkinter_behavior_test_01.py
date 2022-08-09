from tkinter import *
from tkinter import ttk

window = Tk()
window.title("FPV Simulator Recording App")
window.geometry('%dx%d+%d+%d' % (480, 280, 0, 0))
window.resizable(False, False)
window.attributes('-topmost', 'false')

btn_start = Button(window, text="Start", command=lambda: print("..."))
btn_start.config(command=lambda: btn_start.config(text="Stop"))
btn_start.place(x=10, y=10)
window.mainloop()