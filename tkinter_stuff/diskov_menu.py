# -*- coding: utf-8 -*-
"""
Created on Tue Mar  5 00:58:38 2019

@author: olive
"""

import tkinter as tk
from tkinter import filedialog
import diskovery_scene_manager

class Menu_Toolbar:
    
	def __init__(self, master):
		self.master = master
		self.opened = False

		self.edit_mode = 0

		menubar = tk.Menu(self.master)
		m_file = tk.Menu(menubar, tearoff=0)
		m_file.add_command(label="New")
		m_file.add_command(label="Open")
		m_file.add_command(label="Save")
		m_file.add_separator()
		m_file.add_command(label="Exit", command=master.destroy) # root.quit
		menubar.add_cascade(label="File", menu=m_file)
		
		m_edit = tk.Menu(menubar, tearoff=0)
		m_edit.add_command(label="Translate")
		m_edit.add_command(label="Rotate")
		m_edit.add_command(label="Scale")
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
		
		master.config(menu=menubar)