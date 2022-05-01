import tkinter as tk
from tkinter import StringVar
from tkinter import ttk

# object of TK()
main = tk.Tk()




# setting geometry of window
# instance
main.geometry("100x100")

name_var = StringVar(value="1")
name_entry = ttk.Entry(textvariable=name_var)

def submit():
    pass

# creating Window
B1 = ttk.Button(main, text="Submit", command=submit)

# Button positioning
B1.pack()

# infinite loop till close
main.mainloop()