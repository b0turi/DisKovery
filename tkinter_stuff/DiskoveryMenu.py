# -*- coding: utf-8 -*-
"""
Created on Tue Mar  5 00:58:38 2019

@author: olive
"""

import tkinter as tk

class DiskoveryMenu:
    
    def __init__(self, root):
        #Set up the window menu for the UI
        self.menubar = tk.Menu(root)
        
        m_file = tk.Menu(self.menubar, tearoff=0)
        m_file.add_command(label="New")
        m_file.add_command(label="Load")
        m_file.add_command(label="Save")
        m_file.add_separator()
        m_file.add_command(label="Exit", command=root.destroy) # root.quit
        self.menubar.add_cascade(label="File", menu=m_file)
        
        m_edit = tk.Menu(self.menubar, tearoff=0)
        m_edit.add_command(label="Copy")
        m_edit.add_command(label="Paste")
        m_edit.add_command(label="Delete")
        m_edit.add_separator()
        m_edit.add_command(label="Preferences")
        self.menubar.add_cascade(label="Edit", menu=m_edit)
        
        m_view = tk.Menu(self.menubar, tearoff=0)
        
        m_view.add_command(label="Properties")
        m_view.add_command(label="Environment")
        m_view.add_command(label="Asset Directory")
        m_view.add_separator()
        m_view.add_command(label="Tools")
        m_view.add_command(label="Console")
        self.menubar.add_cascade(label="View", menu=m_view)
        
        m_help = tk.Menu(self.menubar, tearoff=0)
        m_help.add_command(label="About DisKovery")
        m_help.add_command(label="Tutorial")
        m_help.add_separator()
        m_help.add_command(label="License")
        self.menubar.add_cascade(label="Help", menu=m_help)
        
        root.config(menu=self.menubar)