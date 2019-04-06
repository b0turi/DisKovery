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
		self.listbox.grid(row=0,column=0)
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
		self.environment.grid(row=0,column=0)
		self.direct1 = tk.Listbox(self.environment, justify = LEFT, height = 20)
		self.direct1.grid(row=0,column=0)
		self.direct1.insert(0, "Hello world!")
	
	def cpu_dir(self, master):
		self.master = master
		self.computer = tk.Frame(self.master, relief = RAISED, borderwidth = 5)
		self.computer.grid(row=1,column=0)
		self.direct2 = tk.Listbox(self.computer, justify = LEFT, height = 20)
		self.direct2.grid(row=0,column=0)
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
		
		self.object_prop = self.object_details()
		
		for x in range(4):
			self.object_prop[x] = tk.Frame(self.master, relief = RAISED, borderwidth = 5, height = 175)
			self.object_prop[x].pack(side = TOP, fill = BOTH)
			self.object_prop[x].pack_propagate(0)
			
		self.default_pos = TripleVector(0,0,0)
		
		self.context_pos(self.object_prop[0])
		self.context_mesh(self.object_prop[1])
		self.context_features(self.object_prop[2])
		self.context_anim(self.object_prop[3])
		print(x)
		
	def object_details(self):
		return [0, 1, 2, 3]
		
		
	def context_pos(self, master):
		self.master = master
		self.title = tk.Label(self.master, text = "Position", font = ("bold"))
		self.title.pack(side = TOP)
		self.position = tk.Label(self.master, text = "Coordinates: ")
		self.position.pack(side = LEFT)
	
		
		self.x = [0,1]
		self.x[0] = tk.Label(self.master, text = "X: ")
		self.x[0].pack(side = LEFT)
		self.x[1] = tk.Entry(self.master, bd = 1, width = 3)
		self.x[1].pack(side = LEFT)
		
		self.y = [0, 1]
		self.y[0] = tk.Label(self.master, text = " Y: ")
		self.y[0].pack(side = LEFT)
		self.y[1] = tk.Entry(self.master, bd = 1, width = 3)
		self.y[1].pack(side = LEFT)
		
		self.z = [0,1]
		self.z[0] = tk.Label(self.master, text = " Z: ")
		self.z[0].pack(side = LEFT)
		self.z[1] = tk.Entry(self.master, bd = 1, width = 3)
		self.z[1].pack(side = LEFT)
		
		self.x[1].insert(0, str(self.default_pos.getX()))
		self.y[1].insert(0, str(self.default_pos.getY()))
		self.z[1].insert(0, str(self.default_pos.getZ()))
		
	
	def context_mesh(self, master):
		self.master = master
		self.title = tk.Label(self.master, text = "Mesh Filter", font = ("bold"))
		self.title.pack(side = TOP)
		
		self.sub1 = tk.Label(self.master, text = "Type: ")
		self.sub1.pack(side=LEFT, fill=X)
		
		self.shape = "Cube"
		self.mesh = tk.Entry(self.master, bd = 1, width = 10)
		self.mesh.pack(side = LEFT, fill = X)
		self.mesh.insert(0,self.shape)
	
	def context_features(self, master):
		self.master = master
		self.title = tk.Label(self.master, text = "Additional Features", font = ("bold"))
		self.title.pack(side = TOP)
		
		self.btnCtnr = tk.Frame(self.master)
		self.btnCtnr.pack(side = RIGHT, fill = Y)
		
		self.condition = tk.Label(self.master, text = "Lighted: ")
		self.condition.pack(anchor = W)
		self.rb = tk.Radiobutton(self.btnCtnr)
		self.rb.pack(anchor = W)
		
		self.condition_1 = tk.Label(self.master, text = "Colored: ")
		self.condition_1.pack(anchor = W)
		self.rb_1 = tk.Radiobutton(self.btnCtnr)
		self.rb_1.pack(anchor = W)
	
	def context_anim(self, master):
		self.master = master
		self.title = tk.Label(self.master, text = "Animations", font = ("bold"))
		self.title.pack(side = TOP)
		
		self.condition = tk.Listbox(self.master, justify = LEFT, height = 20)
		self.condition.pack(fill = BOTH)
	
class TripleVector:
	x = 0
	y = 0
	z = 0
	
	def __init__(self, x, y, z):
		self.x = float(x)
		self.y = float(y)
		self.z = float(z)
		
	def getX(self):
		return self.x
	
	def getY(self):
		return self.y
	
	def getZ(self):
		return self.z
			

