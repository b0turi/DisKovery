# -*- coding: utf-8 -*-
"""
Created on Fri Feb 15 13:48:59 2019

@author: olive
"""

import tkinter as tk
#from PIL import Image, ImageTk

root = tk.Tk()

xtk = tk.Label(root, text = "First").grid(row=0, sticky='W')
ytk = tk.Label(root, text = "Second").grid(row=1, sticky='W')

e1 = tk.Entry(root)
e2 = tk.Entry(root)

e1.grid(row=0, column=1)
e2.grid(row=1, column=1)

while(True):
    root.update()