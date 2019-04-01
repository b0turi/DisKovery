import diskovery
from diskovery import Camera, Entity, RenderedEntity, AnimatedEntity
from diskovery_entities import *

def save_scene(filename, scene_name):
	diskovery._save_scene(filename, scene_name)

def load_scene(filename):
	global _classes

	func_map = { 'Meshes': diskovery.add_mesh,
	 'Textures': diskovery.add_texture, 
	 'Shaders': diskovery.add_shader, 
	 'Animations': diskovery.add_animation,
	 'Camera': diskovery.set_camera_settings,
	 'Entities': diskovery.add_entity }

	filled = []

	with open(filename, 'r') as f:
		current = None
		title = f.readline()[:-1]
		current = f.readline()[:-1]

		line = f.readline()[:-1]

		while len(filled) < len(func_map):
			while line and not line in func_map.keys():

				args = line.split(' ')
				if args[0] != 'E':
					cmd = "func_map[current]("
					for i in range(0, len(args)):
						if args[i] == 'T':
							cmd += "True,"
						elif args[i] == 'F':
							cmd += "False,"
						elif ',' in args[i]:
							cmd += "{},".format(tuple(float(x) for x in args[i].split(',')))
						else:
							cmd += "args[{}],".format(i)
					cmd = cmd[:-1] + ")"
					exec(cmd)
					line = f.readline()[:-1]
				else:
					class_type = diskovery.get_class(args[1])

					cmd = "func_map[current]({}(".format(class_type.__name__)

					sub_line = f.readline()[:-1]
					while sub_line and sub_line[:2] != 'E ':
						param = tuple(sub_line.split(' '))
						if param[0][0] != '\"' and param[0][:2] != '0x':
							param = tuple([float(x) for x in param])
						cmd += str(param[0]) if len(param) == 1 else str(param)
						cmd += ","

						sub_line = f.readline()[:-1]

					cmd = cmd[:-1] + "), \"{}\")".format(args[2])
					exec(cmd) 
					line = sub_line

				if not line:
					break

			filled.append(current)
			current = line

			line = f.readline()[:-1]