#import statements
import tkinter as tk
from tkinter import *
import os

class Display:

	def __init__(self, master, width, height, x, y):
		self.master = master
		
		self.width = width
		self.height = height
		self.x = x
		self.y = y
		self.dim = "{0}{1}{2}{3}{4}{5}{6}".format(str(self.width),'x',str(self.height),
													 '+',str(self.x),'+',str(self.y))
		self.master.geometry(self.dim)
		
		self.master.title('DisKovery Engine v0.01')
		
		self.listbox = tk.Listbox(self.master, justify = CENTER, width = 50)
		self.listbox.pack()
		self.listbox.insert (0, "Hello World!")
		
		self.menu1 = tk.Toplevel(self.master)
		self.menu2 = tk.Toplevel(self.master)
		
		self.directory = Directory(self.menu1, int(self.width/3), self.height, 0, self.y)
		self.context = Context(self.menu2, int(self.width/3), self.height, int(4 * self.x) - 5, self.y)
		
		
		
		
class Directory:
	def __init__(self, master, width, height, x, y):
		self.master = master
		
		self.width = width
		self.height = height
		self.x = x
		self.y = y
		self.dim = "{0}{1}{2}{3}{4}{5}{6}".format(str(self.width),'x',str(self.height),
													 '+',str(self.x),'+',str(self.y))
		self.master.geometry(self.dim)
		
		self.dim_dir = "{0}{1}{2}{3}{4}{5}{6}".format(str(self.width),'x',str(self.height),
													 '+',str(self.x),'+',str(self.y))
		self.master.title('Directory')
		
		self.submenu1 = self.envir_dir(self.master)
		self.submenu = self.cpu_dir(self.master)
	
	def envir_dir(self, master):
		self.master = master
		self.environment = tk.Frame(self.master, relief = RAISED, borderwidth = 5)
		self.environment.pack(side = TOP, fill = BOTH)
		self.direct1 = tk.Listbox(self.environment, justify = LEFT, height = 20)
		self.direct1.pack(fill = BOTH)
		self.direct1.insert(0, "Hello world!")
	
	def cpu_dir(self, master):
		self.master = master
		self.computer = tk.Frame(self.master, relief = RAISED, borderwidth = 5)
		self.computer.pack(side = BOTTOM, fill = BOTH)
		self.direct2 = tk.Listbox(self.computer, justify = LEFT, height = 20)
		self.direct2.pack(fill = BOTH)
		self.direct2.insert(0, "Hello world!")
		
class Context:
	def __init__(self, master, width, height, x, y):
		self.master = master
		
		self.width = width
		self.height = height
		self.x = x
		self.y = y
		self.dim = "{0}{1}{2}{3}{4}{5}{6}".format(str(self.width),'x',str(self.height),
													 '+',str(self.x),'+',str(self.y))
		self.master.geometry(self.dim)
		
		self.dim_dir = "{0}{1}{2}{3}{4}{5}{6}".format(str(self.width),'x',str(self.height),
													 '+',str(int(self.x)),'+',str(self.y))
		self.master.title('Context Menu')
		
		for x in range(3):
			self.context_gen(self.master)
		
		
	def context_gen(self, master):
		self.master = master
		self.context_win = tk.Frame(self.master, relief = RAISED, borderwidth = 5, height = 200)
		self.context_win.pack(side = TOP, fill = BOTH)
	
	def object_details():
		print(1)
