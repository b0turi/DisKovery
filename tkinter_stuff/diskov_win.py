#import statements
import tkinter as tk
from tkinter import *
import os

sys.path.append(os.path.abspath('../engine_core/'))
import diskovery
import diskovery_scene_manager

_selected = None

def update_window(self):
	global _selected
	
	name, current = diskovery.get_selected()

	if current != None:
		if _selected != current:

			self.context_window.fill(diskovery_scene_manager.arguments(name))
			_selected = current
	elif current == None and len(self.context_window.props) > 0:
		_selected = None
		self.context_window.fill({ })


class Display:

	def callback(self):
		self.master.destroy()
		self.endfunc()

	def __init__(self, master, endfunc):
		master.wm_state('zoomed')
		master.iconbitmap("diskovery.ico")	
		master.protocol("WM_DELETE_WINDOW", self.callback)


		self.master = master
		self.endfunc = endfunc
		
		self.width, self.height = (master.winfo_screenwidth(), master.winfo_screenheight())

		self.x = 0
		self.y = 0

		self.master.title('DisKovery Engine v0.01')
		
		dir_frame = tk.Frame(master, width = self.width * 0.12, height = self.height)
		self.dir = Directory(dir_frame, self.width)
		dir_frame.pack(fill=BOTH, side=LEFT, expand=False)

		self.embed = tk.Frame(master, width = self.width * 0.76, height = self.height)
		self.embed.pack(fill=BOTH, side=LEFT)

		con_frame = tk.Frame(master, width = self.width * 0.12, height = self.height)
		self.con = Context(con_frame, self.width, master)
		con_frame.pack(fill=BOTH, side=LEFT, expand=False)

		setattr(master, 'update_window', update_window)
		setattr(master, 'context_window', self.con)

		
class Directory:
	def __init__(self, master, width):
		self.master = master
		
		self.assets_label = tk.Label(self.master, text="Assets", font=("Arial", 12))
		self.assets_label.pack()
		self.assets = tk.Listbox(self.master, width = int(width * 0.02))
		self.assets.pack(fill=BOTH, expand=True)
		self.assets.insert(0, "Hello world!sdfg")


		self.env_label = tk.Label(self.master, text="Environment", font=("Arial", 12))
		self.env_label.pack()
		self.env = tk.Listbox(self.master)
		self.env.pack(fill=BOTH, expand=True)
		self.env.insert(0, "Hello world!qwer")
		
class Context:
	def __init__(self, master, width, root):
		self.master = master
		
		self.context_label = tk.Label(self.master, 
			text="Object Properties", 
			font=("Arial", 12))
		self.context_label.pack()

		# self.object_prop = self.object_details()
		
		# for x in range(4):
		# 	self.object_prop[x] = tk.Frame(self.master, height = 175)
		# 	self.object_prop[x].pack(side = TOP, fill = BOTH, expand=True)
		# 	self.object_prop[x].pack_propagate(0)
			
		self.default_pos = TripleVector(0,0,0)

		self.properties = tk.Frame(self.master, width = int(width*0.02))
		self.properties.pack(fill=BOTH, expand=True)

		self.props = []
		
		# self.context_pos(self.object_prop[0])
		# self.context_mesh(self.object_prop[1])
		# self.context_features(self.object_prop[2])
		# self.context_anim(self.object_prop[3])
		# print(x)
		

	def fill(self, data):


		for prop in self.props:
			prop.destroy()

		i = 1
		for prop, val in data.items():
			# 3D Vector
			if 'tuple' in str(type(val)) and len(val) == 3:
				self.vector_prop(prop, val, i)
			if 'float' in str(type(val)):
				print("Float")
			if 'str' in str(type(val)):
				print("String")

			i += 1


	def vector_prop(self, name, data, num):

		prop = tk.Frame(self.properties)

		prop.columnconfigure(0, weight=3, pad=5)
		prop.columnconfigure(1, weight=1, pad=5)
		prop.columnconfigure(2, weight=1, pad=5)
		prop.columnconfigure(3, weight=1, pad=5)


		self.title = tk.Label(prop, text=name, anchor=W)
		self.title.grid(row=1, column=0, sticky=E)
	
		
		self.x = [0,1]
		self.x[0] = tk.Label(prop, text="X")
		self.x[0].grid(row=0, column=1)
		self.x[1] = tk.Entry(prop, bd = 1, width = 6)
		self.x[1].grid(row=1, column=1)
		
		self.y = [0,1]
		self.y[0] = tk.Label(prop, text="Y")
		self.y[0].grid(row=0, column=2)
		self.y[1] = tk.Entry(prop, bd = 1, width = 6)
		self.y[1].grid(row=1, column=2)
		
		self.z = [0,1]
		self.z[0] = tk.Label(prop, text="Z")
		self.z[0].grid(row=0, column=3)
		self.z[1] = tk.Entry(prop, bd = 1, width = 6)
		self.z[1].grid(row=1, column=3)

		
		self.x[1].insert(0, str(data[0]))
		self.y[1].insert(0, str(data[1]))
		self.z[1].insert(0, str(data[2]))

		prop.pack()

		self.props.append(prop)
		
	
	def string_prop(self, master):
		self.master = master
		self.title = tk.Label(self.master, text = "Mesh Filter", font = ("bold"))
		self.title.pack(side = TOP)
		
		self.sub1 = tk.Label(self.master, text = "Type: ")
		self.sub1.pack(side=LEFT, fill=X)
		
		self.shape = "Cube"
		self.mesh = tk.Entry(self.master, bd = 1, width = 10)
		self.mesh.pack(side = LEFT, fill = X)
		self.mesh.insert(0,self.shape)
	
	def bool_prop(self, master):
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
	
	def list_prop(self, master):
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
			

