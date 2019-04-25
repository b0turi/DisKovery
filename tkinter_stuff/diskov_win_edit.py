#import statements
import tkinter as tk
import inspect
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
import os
import pygame
import ctypes

sys.path.append(os.path.abspath('../engine_core/'))
import diskovery
import diskovery_scene_manager

from diskovery_entities import SelectableEntity

_selected = None
_root = None

def update_window(self):
	global _selected
	
	self.directory_window.update(diskovery_scene_manager.names())

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

	if top_counts(self.directory_window.assets) != diskovery_scene_manager.asset_count() or self.asset_refresh:
		self.directory_window.asset_update(diskovery_scene_manager.get_assets())
		self.asset_refresh = False

def top_counts(tree):
	counts = []
	for child in tree.get_children():
		counts.append(len(tree.get_children(child)))

	return tuple(counts)

def lose_focus(self):
	deselect(self.directory_window.env)

def lose_embed():
	global _root
	_root.embed_focus = False

class Display:

	def callback(self):
		self.master.destroy()
		self.endfunc()

	def __init__(self, master, endfunc):
		global _root
		_root = master

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
		self.embed = tk.Frame(master, width = self.width * 0.76, height = self.height)
		self.embed.pack(fill=BOTH, side=LEFT)

		con_frame = tk.Frame(master, width = self.width * 0.12, height = self.height)
		self.con = Context(con_frame, self.width, master)
		con_frame.pack(fill=BOTH, side=LEFT, expand=False)

		setattr(master, 'update_window', update_window)
		setattr(master, 'context_window', self.con)
		setattr(master, 'directory_window', self.dir)
		setattr(master, 'embed_window', self.embed)
		setattr(master, 'lose_focus', lose_focus)
		setattr(master, 'asset_refresh', False)

		self.dir.asset_update(diskovery.get_all_assets())

def deselect(e):
	if hasattr(e, 'widget'):
		e.widget.selection_clear(0, END)
	else:
		e.selection_clear(0, END)

def select(e):
	global _selected, _root

	if len(e.widget.curselection()) == 0:
		return
	new_ind = e.widget.curselection()[0]

	new_name = None
	for name, index in e.widget.parent.entities.items():
		if index == new_ind:
			new_name = name
			break

	diskovery.select(new_name)
	
	force_click(960,540, False)
	force_click(960,540)


def warning_message(message):
	popup = Tk()

	_root.embed_focus = False

	popup.minsize(width=600, height=100)
	popup.title('Warning')
	popup.iconbitmap("diskovery.ico")
	popup.geometry("+{}+{}".format(660,490))
	popup.resizable(width=0, height=0)

	def restore(e=None):
		popup.destroy()
		_root.embed_focus = True

	popup.protocol("WM_DELETE_WINDOW", restore)

	warning_text = Label(popup, text=message)
	warning_text.pack(fill=X, expand=True, padx=20)

	ok_button = Button(popup, text="OK")
	ok_button.pack(pady=20)

	ok_button.bind('<Button-1>', restore)

def file_entry(parent, label, title, type_desc, types, row_num, default=None):
	label = Label(parent, text=label)
	entry = Entry(parent)
	browse = Button(parent, text="Browse")

	def fill(e):
		entry.delete(0, 'end')
		entry.insert(0, filedialog.askopenfilename(
			parent=parent,
			initialdir='.', 
			title=title, 
			filetypes=[
				(type_desc, types)
			]))
		entry.focus()
	browse.bind("<Button-1>", fill)

	if default != None:
		entry.insert(0, default)

	label.grid(row=row_num, column=0)
	entry.grid(row=row_num, column=1)
	browse.grid(row=row_num, column=2)

	return entry

def string_entry(parent, label, row_num, default=None):
	l = Label(parent, text=label)
	e = Entry(parent)

	if default != None:
		e.insert(0, default)

	l.grid(row=row_num, column=0)
	e.grid(row=row_num, column=1)

	return e

def mesh_form(parent, popup, action, data=None, base_name=None):
	file = file_entry(parent, 
		"Filename:", "Mesh Filename", 
		"3D Models (.obj or .dae)", "*.obj;*.dae", 1,
		None if data == None else data[0]
	)

	name = string_entry(parent, "Mesh Name:", 2,
		None if data == None else data[1])

	animated = IntVar()
	animated_check = Checkbutton(parent, text="Animated Mesh", variable=animated)
	animated_check.grid(row=3, column=1)

	if data != None:
		animated.set(data[2])

	def add_mesh(e):
		global _root
		diskovery.add_mesh(
			file.get(), 
			name.get(), 
			animated.get(), 
			False,
			(action != 'Add'),
			base_name
		)
		popup.destroy()
		_root.embed_focus = True
		_root.asset_refresh = True
		diskovery.refresh()

	add_button = Button(parent, text="{} Mesh".format(action))
	add_button.bind('<Button-1>', add_mesh)
	add_button.grid(row=4, column=1)

def shader_form(parent, popup, action, data=None, base_name=None):
	vert = file_entry(parent, 
		"Vertex Shader:", "Vertex Shader Filename", 
		"GLSL Vertex Shaders (.vert, .glsl)", "*.vert;*.glsl", 1,
		None if data == None else data[0]
	)

	frag = file_entry(parent, 
		"Fragment Shader:", "Fragment Shader Filename", 
		"GLSL Fragment Shaders (.frag, .glsl)", "*.frag;*.glsl", 2,
		None if data == None else data[1]
	)

	name = string_entry(parent, "Shader Name:", 3,
		None if data == None else data[2])

	def add_shader(e):
		global _root
		diskovery_scene_manager.add_shader(
			os.path.basename(vert.get()), 
			os.path.basename(frag.get()), 
			name.get(),
			(action != 'Add'),
			base_name
		)
		popup.destroy()
		_root.embed_focus = True
		_root.asset_refresh  = True

	add_button = Button(parent, text="{} Shader".format(action))
	add_button.bind('<Button-1>', add_shader)
	add_button.grid(row=4, column=1)

def texture_form(parent, popup, action, data=None, base_name=None):
	file = file_entry(parent, 
		"Filename:", "Image Filename", 
		"Image Files", "*.png;*.jpg;*.gif;*.bmp;*.tiff", 1,
		None if data == None else data[0]
	)

	name = string_entry(parent, "Texture Name:", 2,
		None if data == None else data[1])

	def add_texture(e):
		global _root
		diskovery.add_texture(
			file.get(), 
			name.get(),
			(action != 'Add'),
			base_name
		)
		popup.destroy()
		_root.embed_focus = True
		diskovery.refresh()
		_root.asset_refresh  = True

	add_button = Button(parent, text="{} Texture".format(action))
	add_button.bind('<Button-1>', add_texture)
	add_button.grid(row=4, column=1)

def animation_form(parent, popup, action, data=None, base_name=None):
	file = file_entry(parent, 
		"Filename:", "Animation Filename", 
		"COLLADA Files (.dae)", "*.dae", 1,
		None if data == None else data[0]
	)

	name = string_entry(parent, "Animation Name:", 2,
		None if data == None else data[1])

	def add_animation(e):
		global _root
		diskovery_scene_manager.add_animation(
			file.get(), 
			name.get(),
			(action != 'Add'),
			base_name
		)
		popup.destroy()
		_root.embed_focus = True
		diskovery.refresh()
		_root.asset_refresh  = True

	add_button = Button(parent, text="{} Animation".format(action))
	add_button.bind('<Button-1>', add_animation)
	add_button.grid(row=4, column=1)

def class_form(parent, restore, action, class_name):
	if diskovery.get_class(class_name) == None:
		message = "{} is not a valid class. Add a class called {}" \
			" to the 'diskovery_entities.py' file or use a different class name."\
			.format(class_name, class_name)
		warning_message(message)
	else:
		class_type = diskovery.get_class(class_name)
		class_args = dict(inspect.getmembers(class_type.__init__.__code__))['co_varnames'][1:]
		entries = []
		entries.append(string_entry(parent, "Name", 0))
		for i, t in enumerate(class_type.types):
			entries.append(string_entry(parent, class_args[i], i+1))

		btn = Button(parent, text="{} Entity".format(action))

		def add_entity(e):
			rendered_entity_params = {
				'position': 	None,
				'rotation': 	None,
				'scale':		None,
				'mesh_str': 	None,
				'textures_str': None,
				'color':		(diskovery_scene_manager.color(),)
			}

			config = {}
			config['type'] = class_type

			if not issubclass(class_type, diskovery.RenderedEntity):

				rendered_entity_params['position'] = \
					tuple([float(x) for x in entries[1].get()[1:-1].split(',') if x != ''])
				config['position'] = rendered_entity_params['position']

				rendered_entity_params['rotation'] = \
					tuple([float(x) for x in entries[2].get()[1:-1].split(',') if x != ''])
				config['rotation'] = rendered_entity_params['rotation']

				rendered_entity_params['scale'] = (0.4, 0.4, 0.4)
				rendered_entity_params['mesh_str'] = "Cube"
				rendered_entity_params['textures_str'] = ["Blank"]
				rendered_entity_params['is_lit'] = (False,)
				rendered_entity_params['name'] = entries[0].get()

				arg_ptr = 2

				while arg_ptr < len(entries) - 1:
					val = entries[arg_ptr + 1].get()
					if '(' in val:
						val = tuple([float(x) for x in val[1:-1].split(',') if x != ''])

					elif class_type.types[arg_ptr] == float:
						val = float(val)
					elif class_type.types[arg_ptr] == int:
						val = int(val)

					config[class_args[arg_ptr]] = val

					arg_ptr += 1

				if class_type == diskovery.Light:
					rendered_entity_params['tint'] = tuple(config['tint']) + (1.0,)
					rendered_entity_params['chi'] = "{}-real".format(entries[0].get())
					diskovery.add_entity(diskovery.Light(
						config['position'],
						config['rotation'],
						config['tint'],
						config['intensity'],
						config['distance'],
						config['spread'],
						config['scene']
					), "{}-real".format(entries[0].get()))

			else:

				for p in range(0, len(entries)-1):
					if class_args[p] in rendered_entity_params.keys():
						rendered_entity_params[class_args[p]] = entries[p+1].get()
						config[class_args[p]] = entries[p+1].get()

				for name, val in class_type.presets.items():
					if name in rendered_entity_params.keys():
						rendered_entity_params[name] = val

				rendered_entity_params['name'] = entries[0].get()

			cmd = "diskovery.add_entity(SelectableEntity("

			for name, val in rendered_entity_params.items():
				cmd += "{}=".format(name)
				cmd_val = val[0] if len(val) == 1 else val
				if 'str' in str(type(val)) and '(' not in val and '[' not in val:
					cmd += "'{}'".format(cmd_val)
				elif 'list' in str(type(val)):
					cmd += "{}".format(val)
				else:
					cmd += "{}".format(cmd_val)
				cmd += ","

			cmd = cmd[:-1] + "), '{}')".format(entries[0].get())

			diskovery_scene_manager.add_config(config, entries[0].get())
			exec(cmd)
			diskovery.select(entries[0].get())
			restore()

		btn.bind('<Button-1>', add_entity)
		btn.grid(row=i+2, column=1)


class Directory:

	def new_asset(self, e):
		global _root 

		popup = Tk()

		_root.embed_focus = False

		popup.minsize(width=400, height=300)
		popup.title('Add New Asset')
		popup.iconbitmap("diskovery.ico")
		popup.geometry("+{}+{}".format(720,390))
		popup.resizable(width=0, height=0)

		def restore(e=None):
			popup.destroy()
			_root.embed_focus = True

		popup.protocol("WM_DELETE_WINDOW", restore)

		contents = Frame(popup)
		contents.columnconfigure(0, weight=1, pad=5)
		contents.columnconfigure(1, weight=2, pad=5)
		contents.columnconfigure(2, weight=1, pad=5)

		def fill_for_type(e):
			
			for widget in contents.winfo_children():
				widget.destroy()
			
			form_map = {
				"Mesh": mesh_form,
				"Shader": shader_form,
				"Texture": texture_form,
				"Animation": animation_form
			}

			form_map[e.widget.get()](contents, popup, "Add")

		a_label = Label(popup, text="Asset Type:", font=("Arial", 12))
		type_value = StringVar(popup)
		type_value.set("Mesh")

		a_type = ttk.Combobox(popup, textvariable=type_value, values = ["Mesh", "Shader", "Texture", "Animation"])
		a_type.bind('<<ComboboxSelected>>', fill_for_type)

		a_label.pack(side=LEFT, padx=5, pady=5)
		a_type.pack(side=LEFT, padx=5, pady=5)

		contents.pack(side=TOP, fill=BOTH, expand=True, pady=15)

	def edit_asset(self, e):
		global _root 

		item = self.assets.focus()
		item_type = self.assets.parent(item)

		if item == '' or item_type == '':
			return

		item = item[len(item_type):]
		asset = diskovery_scene_manager.get_asset(item_type, item)

		extract_map = {
			"Meshes": '(asset.filename, item, hasattr(asset, "rig"))',
			"Shaders": '(asset.sources[0], asset.sources[1], item)',
			"Textures": '(asset.filename, item)',
			"Animations": '(asset.filename, item)'
		}

		form_map = {
			"Meshes": mesh_form,
			"Shaders": shader_form,
			"Textures": texture_form,
			"Animations": animation_form
		}

		popup = Tk()

		_root.embed_focus = False

		popup.minsize(width=400, height=300)
		popup.title('Edit Asset')
		popup.iconbitmap("diskovery.ico")
		popup.geometry("+{}+{}".format(720,390))
		popup.resizable(width=0, height=0)

		def restore(e=None):
			popup.destroy()
			_root.embed_focus = True

		popup.protocol("WM_DELETE_WINDOW", restore)

		contents = Frame(popup)
		contents.columnconfigure(0, weight=1, pad=5)
		contents.columnconfigure(1, weight=2, pad=5)
		contents.columnconfigure(2, weight=1, pad=5)

		form_map[item_type](contents, popup, "Update", eval(extract_map[item_type]), item)

		contents.pack(side=TOP, fill=BOTH, expand=True, pady=15)

	def delete_asset(self, e):
		item = self.assets.focus()
		item_type = self.assets.parent(item)

		if item == '' or item_type == '':
			return

		item = item[len(item_type):]
		asset = diskovery_scene_manager.get_asset(item_type, item)

		if diskovery_scene_manager.is_used(item_type, item):
			warning_message("This asset is being used by an entity in the scene. "\
				"Remove all entities using this asset from the scene before deleting it.")
			return

		remove_map = {
			"Meshes": diskovery.remove_mesh,
			"Textures": diskovery.remove_texture,
			"Animations": diskovery_scene_manager.remove_animation,
			"Shaders": diskovery_scene_manager.remove_shader
		}

		remove_map[item_type](item)

	def new_entity(self, e):
		popup = Tk()

		_root.embed_focus = False

		popup.minsize(width=400, height=300)
		popup.title('Edit Entity')
		popup.iconbitmap("diskovery.ico")
		popup.geometry("+{}+{}".format(720,390))
		popup.resizable(width=0, height=0)

		def restore(e=None):
			popup.destroy()
			_root.embed_focus = True

		popup.protocol("WM_DELETE_WINDOW", restore)

		contents = Frame(popup)
		contents.columnconfigure(0, weight=1, pad=5)
		contents.columnconfigure(1, weight=2, pad=5)
		contents.columnconfigure(2, weight=1, pad=5)

		def fill_class_reqs(e):
			class_form(contents, restore, "Add", e.widget.get())

		e_label = Label(popup, text="Class Name:", font=("Arial", 12))

		e_class = Entry(popup)
		e_class.bind('<Return>', fill_class_reqs)

		def root_lose(e):
			_root.embed_focus = False
		e_class.bind('<Button-1>', root_lose)
		e_class.bind('<Key>', root_lose)

		e_label.pack(side=LEFT, padx=5, pady=5)
		e_class.pack(side=LEFT, padx=5, pady=5)

		contents.pack(side=TOP, fill=BOTH, expand=True, pady=15)

	def delete_entity(self, e):
		global _selected, _root
		item = self.env.curselection()[0]

		print(diskovery.entity(self.env.get(item)).chi)
		if diskovery.entity(self.env.get(item)).chi != None:
			diskovery.remove_entity(diskovery.entity(self.env.get(item)).chi)

		diskovery.remove_entity(self.env.get(item))
		diskovery_scene_manager.remove_config(self.env.get(item))

		self.env.delete(item)
		diskovery.deselect()
		_selected = None

	def open_branch(self, e):
		item = self.assets.focus()
		self.open_states[item] = True

	def close_branch(self, e):
		item = self.assets.focus()
		self.open_states[item] = False

	def __init__(self, master, width):
		self.master = master
		
		self.open_states = {'Meshes': False, 'Shaders': False, 'Textures': False, 'Animations': False}

		self.assets_label = tk.Label(self.master, text="Assets", font=("Arial", 12))
		self.assets_label.pack()
		self.assets = ttk.Treeview(self.master)
		self.assets.pack(fill=BOTH, expand=True)

		assets_scroll = ttk.Scrollbar(self.assets, orient="vertical", command=self.assets.yview)
		assets_scroll.pack(fill=Y, side=RIGHT, expand=False)

		self.assets.configure(yscrollcommand=assets_scroll.set)
		self.assets.bind('<<TreeviewOpen>>', self.open_branch)
		self.assets.bind('<<TreeviewClose>>', self.close_branch)
		self.assets.bind('<Double-Button-1>', self.edit_asset)

		asset_menu = Frame(self.master)
		add_asset = Button(asset_menu, text="New Asset", font=("Arial", 10))
		add_asset.grid(row=0, column=0)
		add_asset.bind('<Button-1>', self.new_asset)

		edit_asset = Button(asset_menu, text="Edit Asset", font=("Arial", 10))
		edit_asset.grid(row=0, column=1)
		edit_asset.bind('<Button-1>', self.edit_asset)

		remove_asset = Button(asset_menu, text="Delete Asset", font=("Arial", 10))
		remove_asset.grid(row=0, column=2)
		remove_asset.bind('<Button-1>', self.delete_asset)

		asset_menu.pack()

		self.entities = { }

		self.env_label = tk.Label(self.master, text="Environment", font=("Arial", 12))
		self.env_label.pack()
		self.env = tk.Listbox(self.master, selectmode=SINGLE)
		self.env.pack(fill=BOTH, expand=True)
		self.env.insert(0, "Hello world!qwer")
		self.env.bind('<<ListboxSelect>>', select)

		env_menu = Frame(self.master)
		add_entity = Button(env_menu, text="New Entity", font=("Arial", 10))
		add_entity.grid(row=0, column=0)
		add_entity.bind('<Button-1>', self.new_entity)

		remove_entity = Button(env_menu, text="Delete Entity", font=("Arial", 10))
		remove_entity.grid(row=0, column=2)
		remove_entity.bind('<Button-1>', self.delete_entity)

		env_menu.pack()

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
			self.assets.insert('', 'end', category, text=category, open=self.open_states[category])
			for name, asset in content.items():
				self.assets.insert(category, 'end', category+name, text=name)

def start_edit(e):
	global _root
	_root.embed_focus = False
	e.widget.editing = True

def stop_edit(e):
	global _selected, _root
	e.widget.editing = False
	
	if e.type == EventType.KeyPress:
		if hasattr(e.widget, 'tuple_bit'):
			diskovery_scene_manager.update_attribute(_selected, e.widget.index, e.widget.get(), e.widget.tuple_bit)
		else:
			diskovery_scene_manager.update_attribute(_selected, e.widget.index, e.widget.get(), type_val=e.widget.type_val)

		_root.embed_focus = True
		_root.embed_window.focus()

		force_click(960, 540)
		diskovery.refresh()

def force_click(x,y,passive = True):
	# Emulate right click to gain focus in the Pygame window
	coords = (ctypes.c_long * 2)()
	ctypes.windll.user32.GetCursorPos(ctypes.byref(coords))
	ctypes.windll.user32.ShowCursor(False)
	ctypes.windll.user32.SetCursorPos(x, y)
	ctypes.windll.user32.mouse_event(32, 0, 0, 0,0)
	ctypes.windll.user32.mouse_event(64, 0, 0, 0,0)
	if passive:
		ctypes.windll.user32.SetCursorPos(coords[0], coords[1])
	ctypes.windll.user32.ShowCursor(True)

class Context:
	def __init__(self, master, width, root):
		self.master = master

		self.context_label = tk.Label(self.master, 
			text="Object Properties", 
			font=("Arial", 12))
		self.context_label.pack()

		self.properties = tk.Frame(self.master, width = int(width*0.02))
		self.properties.pack(fill=BOTH, expand=True)
		self.props = []

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
				self.float_prop(prop, val, i)
			if 'int' in str(type(val)):
				self.int_prop(prop, val, i)
			if 'str' in str(type(val)):
				self.string_prop(prop, val, i)
			if 'list' in str(type(val)):
				self.list_prop(prop, val, i)

			i += 1

	def update(self, data):

		for i, val in enumerate(data.values()):
			if 'tuple' in str(type(val)) and len(val) == 3:
				if not self.props[i].x_entry.editing:
					self.props[i].x.set(str(val[0]))
				if not self.props[i].y_entry.editing:
					self.props[i].y.set(str(val[1]))
				if not self.props[i].z_entry.editing:
					self.props[i].z.set(str(val[2]))

			elif 'str' in str(type(val)):
				if not self.props[i].val_entry.editing:
					self.props[i].value.set(val)

			elif 'int' in str(type(val)):
				if not self.props[i].val_entry.editing:
					self.props[i].value.set(val)

			elif 'float' in str(type(val)):
				if not self.props[i].val_entry.editing:
					self.props[i].value.set(val)

			elif 'list' in str(type(val)):
				if not self.props[i].val_entry.editing:
					self.props[i].value.set(','.join(val))


	def vector_prop(self, name, data, num):
		prop = tk.Frame(self.properties)

		prop.columnconfigure(0, weight=3, pad=5)
		prop.columnconfigure(1, weight=1, pad=5)
		prop.columnconfigure(2, weight=1, pad=5)
		prop.columnconfigure(3, weight=1, pad=5)

		self.title = tk.Label(prop, text=name, anchor=W)
		self.title.grid(row=1, column=0, sticky=E)
		
		x = [0,1]
		x_val = DoubleVar()
		x[0] = tk.Label(prop, text="X")
		x[0].grid(row=0, column=1)
		x[1] = tk.Entry(prop, bd = 1, width = 6, textvariable=x_val)
		x[1].bind("<Button-1>", start_edit)
		x[1].bind("<FocusIn>", start_edit)
		x[1].bind("<Return>", stop_edit)
		x[1].bind("<FocusOut>", stop_edit)
		x[1].bind("<Escape>", stop_edit)
		x[1].grid(row=1, column=1)
		setattr(prop, 'x', x_val)
		setattr(prop, 'x_entry', x[1])
		setattr(x[1], 'editing', False)
		setattr(x[1], 'index', num)
		setattr(x[1], 'tuple_bit', 0)

		
		y = [0,1]
		y_val = DoubleVar()
		y[0] = tk.Label(prop, text="Y")
		y[0].grid(row=0, column=2)
		y[1] = tk.Entry(prop, bd = 1, width = 6, textvariable=y_val)
		y[1].bind("<Button-1>", start_edit)
		y[1].bind("<FocusIn>", start_edit)
		y[1].bind("<Return>", stop_edit)
		y[1].bind("<FocusOut>", stop_edit)
		y[1].bind("<Escape>", stop_edit)
		y[1].grid(row=1, column=2)
		setattr(prop, 'y', y_val)
		setattr(prop, 'y_entry', y[1])
		setattr(y[1], 'editing', False)
		setattr(y[1], 'index', num)
		setattr(y[1], 'tuple_bit', 1)

		
		z = [0,1]
		z_val = DoubleVar()
		z[0] = tk.Label(prop, text="Z")
		z[0].grid(row=0, column=3)
		z[1] = tk.Entry(prop, bd = 1, width = 6, textvariable=z_val)
		z[1].bind("<Button-1>", start_edit)
		z[1].bind("<FocusIn>", start_edit)
		z[1].bind("<Return>", stop_edit)
		z[1].bind("<FocusOut>", stop_edit)
		z[1].bind("<Escape>", stop_edit)
		z[1].grid(row=1, column=3)
		setattr(prop, 'z', z_val)
		setattr(prop, 'z_entry', z[1])
		setattr(z[1], 'editing', False)
		setattr(z[1], 'index', num)
		setattr(z[1], 'tuple_bit', 2)

		prop.pack()

		self.props.append(prop)
		
	
	def string_prop(self, name, data, num):
		
		prop = tk.Frame(self.properties)
		self.title = tk.Label(prop, text=name, anchor=W)
		self.title.grid(row=0, column=0, sticky=E)
		
		str_val = StringVar()
		value = tk.Entry(prop, bd = 1, width = 10, textvariable=str_val)
		value.bind("<Button-1>", start_edit)
		value.bind("<FocusIn>", start_edit)
		value.bind("<Return>", stop_edit)
		value.bind("<FocusOut>", stop_edit)
		value.bind("<Escape>", stop_edit)
		value.grid(row=0, column=1)
		value.insert(0,data)
		prop.pack()

		setattr(prop, 'value', str_val)
		setattr(prop, 'val_entry', value)
		setattr(value, 'editing', False)
		setattr(value, 'index', num)
		setattr(value, 'type_val', 'string')

		self.props.append(prop)

	def float_prop(self, name, data, num):
		
		prop = tk.Frame(self.properties)
		self.title = tk.Label(prop, text=name, anchor=W)
		self.title.grid(row=0, column=0, sticky=E)
		
		dbl_val = DoubleVar()
		value = tk.Entry(prop, bd = 1, width = 10, textvariable=dbl_val)
		value.bind("<Button-1>", start_edit)
		value.bind("<FocusIn>", start_edit)
		value.bind("<Return>", stop_edit)
		value.bind("<FocusOut>", stop_edit)
		value.bind("<Escape>", stop_edit)
		value.grid(row=0, column=1)
		value.insert(0,data)
		prop.pack()

		setattr(prop, 'value', dbl_val)
		setattr(prop, 'val_entry', value)
		setattr(value, 'editing', False)
		setattr(value, 'index', num)
		setattr(value, 'type_val', 'float')

		self.props.append(prop)

	def int_prop(self, name, data, num):
		
		prop = tk.Frame(self.properties)
		self.title = tk.Label(prop, text=name, anchor=W)
		self.title.grid(row=0, column=0, sticky=E)
		
		int_val = IntVar()
		value = tk.Entry(prop, bd = 1, width = 10, textvariable=int_val)
		value.bind("<Button-1>", start_edit)
		value.bind("<FocusIn>", start_edit)
		value.bind("<Return>", stop_edit)
		value.bind("<FocusOut>", stop_edit)
		value.bind("<Escape>", stop_edit)
		value.grid(row=0, column=1)
		value.insert(0,data)
		prop.pack()

		setattr(prop, 'value', int_val)
		setattr(prop, 'val_entry', value)
		setattr(value, 'editing', False)
		setattr(value, 'index', num - 1)
		setattr(value, 'type_val', 'int')

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
	
	def list_prop(self, name, data, num):
		prop = tk.Frame(self.properties)
		self.title = tk.Label(prop, text=name, anchor=W)
		self.title.grid(row=0, column=0, sticky=E)
		
		str_val = StringVar()
		value = tk.Entry(prop, bd = 1, width = 10, textvariable=str_val)
		value.bind("<Button-1>", start_edit)
		value.bind("<FocusIn>", start_edit)
		value.bind("<Return>", stop_edit)
		value.bind("<FocusOut>", stop_edit)
		value.bind("<Escape>", stop_edit)
		value.grid(row=0, column=1)
		value.insert(0,','.join(data))
		prop.pack()

		setattr(prop, 'value', str_val)
		setattr(prop, 'val_entry', value)
		setattr(value, 'editing', False)
		setattr(value, 'index', num - 1)
		setattr(value, 'type_val', 'list')

		self.props.append(prop)
	
