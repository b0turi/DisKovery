#import statements
import tkinter as tk
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
import os
import pygame

sys.path.append(os.path.abspath('../engine_core/'))
import diskovery
import diskovery_scene_manager

_selected = None

def update_window(self):
	global _selected
	
	name, current = diskovery.get_selected()

	if current != None:

		if self.directory_window.env.curselection() != self.directory_window.entities[name]:
			deselect(self.directory_window.env)
			self.directory_window.env.selection_set(self.directory_window.entities[name])

		if _selected != name:

			self.context_window.fill(diskovery_scene_manager.arguments(name))
			_selected = name
		
	elif current == None and len(self.context_window.props) > 0:
		_selected = None
		self.context_window.fill({ })
	elif current == None and len(self.directory_window.env.curselection()) != 0:
		deselect(self.directory_window.env)

	if _selected != None:
		self.context_window.update(diskovery_scene_manager.arguments(name))

	self.directory_window.update(diskovery_scene_manager.names())

	if top_counts(self.directory_window.assets) != diskovery.asset_count():
		self.directory_window.asset_update(diskovery.get_all_assets())

def top_counts(tree):
	counts = []
	for child in tree.get_children():
		counts.append(len(tree.get_children(child)))

	return tuple(counts)

def lose_focus(self):
	deselect(self.directory_window.env)

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
		setattr(self.dir, 'parent', master)

		setattr(master, 'embed_focus', True)

		def set_focus(val):
			master.embed_focus = val

		self.embed = tk.Frame(master, width = self.width * 0.76, height = self.height)
		self.embed.pack(fill=BOTH, side=LEFT)
		self.embed.bind('<Enter>', lambda e: set_focus(True))
		self.embed.bind('<Leave>', lambda e: set_focus(False))

		con_frame = tk.Frame(master, width = self.width * 0.12, height = self.height)
		self.con = Context(con_frame, self.width, master)
		con_frame.pack(fill=BOTH, side=LEFT, expand=False)

		setattr(master, 'update_window', update_window)
		setattr(master, 'context_window', self.con)
		setattr(master, 'directory_window', self.dir)
		setattr(master, 'lose_focus', lose_focus)

		self.dir.asset_update(diskovery.get_all_assets())

def deselect(e):
	if hasattr(e, 'widget'):
		e.widget.selection_clear(0, END)
	else:
		e.selection_clear(0, END)

def select(e):
	global _selected

	new_ind = e.widget.curselection()[0]
	new_name = None

	if _selected != None:
		indices = e.widget.curselection()

		for ind in indices:
			if ind != e.widget.parent.entities[_selected]:
				new_ind = ind
				break

	for name, index in e.widget.parent.entities.items():
		if index == new_ind:
			new_name = name
			break

	e.widget.selection_clear(0, END)
	e.widget.selection_set(new_ind)

	e.widget.parent.parent.embed_focus = True
	# Simulate right click to gain focus in the Pygame window
	rclick = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 2})
	pygame.event.post(rclick)

	diskovery.select(new_name)
	diskovery.draw()


def new_asset(e):
	popup = Tk()

	popup.minsize(width=400, height=300)
	popup.title('Add New Asset')
	popup.iconbitmap("diskovery.ico")
	popup.geometry("+{}+{}".format(720,390))
	popup.resizable(width=0, height=0)

	def fill_for_type(e):
		
		if e.widget.get() == "Mesh":
			filename_label = Label(popup, text="Filename:")
			filename_entry = Entry(popup)
			filename_browse = Button(popup, text="Browse")

			def fill_filename(e):
				filename_entry.insert(0, filedialog.askopenfilename(
					initialdir='.', 
					title="Mesh Filename", 
					filetypes=[
						("3D Models (.obj and .dae)", "*.obj;*.dae")
					]))
				filename_entry.focus()
			filename_browse.bind("<Button-1>", fill_filename)

			filename_label.grid(row=1, column=0)
			filename_entry.grid(row=1, column=1)
			filename_browse.grid(row=1, column=2)

			mesh_name_label = Label(popup, text="Name:")
			mesh_name_entry = Entry(popup)

			mesh_name_label.grid(row=2, column=0)
			mesh_name_entry.grid(row=2, column=1)

			animated = IntVar()
			animated_check = Checkbutton(popup, text="Animated Mesh", variable=animated)
			animated_check.grid(row=3, column=1)

			add_button = Button(popup, text="Add The Man")

	a_label = Label(popup, text="Asset Type:", font=("Arial", 12))

	type_value = StringVar(popup)
	type_value.set("Mesh")

	a_type = ttk.Combobox(popup, textvariable=type_value, values = ["Mesh", "Shader", "Texture", "Animation"])
	a_type.bind('<<ComboboxSelected>>', fill_for_type)

	a_label.grid(row=0, column=0)
	a_type.grid(row=0, column=1)

class Directory:
	def __init__(self, master, width):
		self.master = master
		
		self.assets_label = tk.Label(self.master, text="Assets", font=("Arial", 12))
		self.assets_label.pack()
		self.assets = ttk.Treeview(self.master)
		self.assets.pack(fill=BOTH, expand=True)
		self.assets.bind('<FocusOut>', deselect)

		assets_scroll = ttk.Scrollbar(self.assets, orient="vertical", command=self.assets.yview)
		assets_scroll.pack(fill=Y, side=RIGHT, expand=False)

		self.assets.configure(yscrollcommand=assets_scroll.set)

		asset_menu = Frame(self.master)
		add_asset = Button(asset_menu, text="New Asset", font=("Arial", 10))
		add_asset.grid(row=0, column=0)
		add_asset.bind('<Button-1>', new_asset)

		edit_asset = Button(asset_menu, text="Edit Asset", font=("Arial", 10))
		edit_asset.grid(row=0, column=1)

		remove_asset = Button(asset_menu, text="Delete Asset", font=("Arial", 10))
		remove_asset.grid(row=0, column=2)

		asset_menu.pack()

		self.entities = { }

		self.env_label = tk.Label(self.master, text="Environment", font=("Arial", 12))
		self.env_label.pack()
		self.env = tk.Listbox(self.master)
		self.env.pack(fill=BOTH, expand=True)
		self.env.insert(0, "Hello world!qwer")
		self.env.bind('<FocusOut>', deselect)
		self.env.bind('<<ListboxSelect>>', select)

		setattr(self.env, 'parent', self)

	def update(self, env_data):
		if len(env_data) != len(self.entities.keys()):
			self.env.delete(0, END)
			self.entity_list = []

			for i, name in enumerate(env_data):
				self.entities[name] = i
				self.env.insert(i, name)

	def asset_update(self, asset_data):
		self.assets.delete(*self.assets.get_children())

		for category, content in asset_data.items():
			self.assets.insert('', 'end', category, text=category)
			for name, asset in content.items():
				self.assets.insert(category, 'end', category+name, text=name)

def start_edit(e):
	e.widget.editing = True

def change_value(e):
	global _selected
	diskovery_scene_manager.update_attribute(_selected, e.widget.index, e.widget.get(), e.widget.tuple_bit)
	e.widget.editing = False
	diskovery.draw()


def stop_edit(e):
	change_value(e)
	e.widget.editing = False

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

		self.props = []

		i = 1
		for prop, val in data.items():
			# 3D Vector
			if 'tuple' in str(type(val)) and len(val) == 3:
				self.vector_prop(prop, val, i)
			if 'float' in str(type(val)):
				self.string_prop(prop, val, i)
			if 'str' in str(type(val)):
				print("String")

			i += 1

	def update(self, data):

		for i, val in enumerate(data.values()):
			if 'tuple' in str(type(val)) and len(val) == 3:
				if not self.props[i].x_entry.editing:
					self.props[i].x.set(str(val[0]))
				if str(val[1]) != self.props[i].y.get():
					self.props[i].y.set(str(val[1]))
				if str(val[2]) != self.props[i].z.get():
					self.props[i].z.set(str(val[2]))


	def vector_prop(self, name, data, num):
		prop = tk.Frame(self.properties)

		prop.columnconfigure(0, weight=3, pad=5)
		prop.columnconfigure(1, weight=1, pad=5)
		prop.columnconfigure(2, weight=1, pad=5)
		prop.columnconfigure(3, weight=1, pad=5)

		self.title = tk.Label(prop, text=name, anchor=W)
		self.title.grid(row=1, column=0, sticky=E)
		
		x = [0,1]
		x_val = StringVar()
		x[0] = tk.Label(prop, text="X")
		x[0].grid(row=0, column=1)
		x[1] = tk.Entry(prop, bd = 1, width = 6, textvariable=x_val)
		x[1].bind("<FocusIn>", start_edit)
		x[1].bind("<Return>", change_value)
		x[1].bind("<FocusOut>", stop_edit)
		x[1].grid(row=1, column=1)
		setattr(prop, 'x', x_val)
		setattr(prop, 'x_entry', x[1])
		setattr(x[1], 'editing', False)
		setattr(x[1], 'index', num - 1)
		setattr(x[1], 'tuple_bit', 0)

		
		y = [0,1]
		y_val = StringVar()
		y[0] = tk.Label(prop, text="Y")
		y[0].grid(row=0, column=2)
		y[1] = tk.Entry(prop, bd = 1, width = 6, textvariable=y_val)
		y[1].grid(row=1, column=2)
		setattr(prop, 'y', y_val)
		setattr(prop, 'y_entry', y[1])

		
		z = [0,1]
		z_val = StringVar()
		z[0] = tk.Label(prop, text="Z")
		z[0].grid(row=0, column=3)
		z[1] = tk.Entry(prop, bd = 1, width = 6, textvariable=z_val)
		z[1].grid(row=1, column=3)
		setattr(prop, 'z', z_val)
		setattr(prop, 'z_entry', z[1])

		prop.pack()

		self.props.append(prop)
		
	
	def string_prop(self, name, data, num):
		
		prop = tk.Frame(self.properties)
		self.title = tk.Label(prop, text=name, anchor=W)
		self.title.grid(row=0, column=0, sticky=E)
		
		self.mesh = tk.Entry(prop, bd = 1, width = 10)
		self.mesh.grid(row=0, column=1)
		self.mesh.insert(0,data)
		prop.pack()

		self.props.append(prop)
	
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
			

