# -*- coding: utf-8 -*-
# !/usr/bin/python3
"""
Created on Mon Feb 11 15:49:35 2019

@author: olive
"""
import tkinter as tk
from tkinter import LEFT,RIGHT,TOP,BOTH,CENTER
from PIL import Image, ImageTk
#import diskovery_grid.py as dg
#from PIL import Image, ImageTk



f_w = 1200 #default width
f_h = 825 #default height

#Settings for the window
root = tk.Tk()
root.geometry('1200x825+0+0')
root.title('DisKovery Engine v0.01')

#Set up the window menu for the UI
menubar = tk.Menu(root)

m_file = tk.Menu(menubar, tearoff=0)
m_file.add_command(label="New")
m_file.add_command(label="Load")
m_file.add_command(label="Save")
m_file.add_separator()
m_file.add_command(label="Exit", command=root.destroy) # root.quit
menubar.add_cascade(label="File", menu=m_file)

m_edit = tk.Menu(menubar, tearoff=0)
m_edit.add_command(label="Copy")
m_edit.add_command(label="Paste")
m_edit.add_command(label="Delete")
m_edit.add_separator()
m_edit.add_command(label="Preferences")
menubar.add_cascade(label="Edit", menu=m_edit)

m_view = tk.Menu(menubar, tearoff=0)

m_view.add_command(label="Properties")
m_view.add_command(label="Environment")
m_view.add_command(label="Asset Directory")
m_view.add_separator()
m_view.add_command(label="Tools")
m_view.add_command(label="Console")
menubar.add_cascade(label="View", menu=m_view)

m_help = tk.Menu(menubar, tearoff=0)
m_help.add_command(label="About DisKovery")
m_help.add_command(label="Tutorial")
m_help.add_separator()
m_help.add_command(label="License")
menubar.add_cascade(label="Help", menu=m_help)

root.config(menu=menubar)

#Set up frames on the sides of the UI for widgets
w1 = tk.Frame(root)
#Assign names to buttons
for r in range(20):
    for c in range(5):
        tk.Button(w1, text = 'Button', borderwidth = 5).grid(row=r,column=c)

w2 = tk.Frame(root)
for r in range(20):
    for c in range(5):
        tk.Button(w2, text = 'Button', borderwidth = 5).grid(row=r,column=c)

projection = Image.open("./vulkan_graphic.gif")
display = ImageTk.PhotoImage(projection)
w3 = tk.Canvas(root, bg="white")

w1.pack(side = LEFT)
w2.pack(side = RIGHT)
w3.pack(side = TOP, fill = BOTH, expand = True)
w3.create_image(f_w/3, f_h/2,anchor=CENTER, image=display)

root.mainloop()

"""
end
"""
