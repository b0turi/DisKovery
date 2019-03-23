# -*- coding: utf-8 -*-
# !/usr/bin/python3
"""
Created on Mon Feb 11 15:49:35 2019

@author: olive
"""
import tkinter as tk
from tkinter import LEFT,RIGHT,TOP,BOTH,CENTER,X,Y,N
import os
import glm
import pygame
import sys
import subprocess

f_w = 1300 #default width
f_h = 825 #default height

#Settings for the window
root = tk.Tk()
root.geometry('1200x825+0+0')
root.title('DisKovery Engine v0.01')

def menusetup():
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

menusetup()
w = tk.Frame(root)
w.pack(side = LEFT, fill=BOTH)

#Set up frames on the sides of the UI for widgets
w1 = tk.Frame(w, height = 50, width = 50)
#Assign
env = tk.Listbox(w1, justify = CENTER, width = 50)
env.grid(row=0,column=0)
env.insert(25, "Environment")
w1.pack(fill = BOTH, expand = True)

w2 = tk.Frame(w, height = 50, width = 50)
direct = tk.Listbox(w2, justify = CENTER, width = 50)
direct.grid(row=0,column=0)
direct.insert(25, "Asset Directories")
direct.insert(25, " ")
w2.pack(fill = BOTH, expand = True)

"""projection = Image.open("./vulkan_graphic.gif")
display = ImageTk.PhotoImage(projection)
w3 = tk.Canvas(root, bg="white", width = "15c")
w3.pack(side=LEFT, fill=BOTH, expand = True)
w3.create_image(f_w/3, f_h/3,anchor=CENTER, image=display)"""
w3_embed = tk.Frame(root, width = 800, height = 450)
w3_embed.pack(side = LEFT, fill=BOTH, expand=True)


env = dict(os.environ)
env['SDL_WINDOWID'] = str(w3_embed.winfo_id())

os.chdir('..')
os.chdir('engine_core')
full_path = os.path.abspath(os.getcwd())

print(full_path)
p = subprocess.run('python main.py', env=env, capture_output=True, check=True, cwd=os.getcwd())

w4 = tk.Frame(root, height = 50, width = 50)
pro = tk.Listbox(w4, justify = CENTER, width = 50)
pro.grid(row=0, column=0)
pro.insert(25, "Properties")
w4.pack(side = RIGHT, fill = Y, expand = True)

root.update()
	
	

"""
end
"""
