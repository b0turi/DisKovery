import ast
import glm
import inspect
import random
import diskovery
from diskovery import Camera, Entity, RenderedEntity, AnimatedEntity, Light, Terrain
from diskovery_entities import *

_entity_configs = { }

def save_scene(filename, scene_name):
	diskovery._save_scene(filename, scene_name)

def load_scene(filename):

	diskovery.clear_environment()

	func_map = { 'Meshes': diskovery.add_mesh,
	 'Textures': diskovery.add_texture,
	 'Shaders': diskovery.add_shader,
	 'Animations': diskovery.add_animation,
	 'Camera': diskovery.set_camera_settings,
	 'LightScenes': diskovery.add_light_scene,
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

						elif param[0][0] == '\"' and ',' in param[0]:
							param = [x[1:-1] for x in param[0].split(',')]

						cmd += str(param[0]) if len(param) == 1 else str(param)
						cmd += ","

						sub_line = f.readline()[:-1]

					cmd = cmd[:-1] + "), \"{}\")".format(args[2])
					print(cmd)
					exec(cmd)
					line = sub_line

				if not line:
					break

			filled.append(current)
			current = line

			line = f.readline()[:-1]

		for i in range(0, 10):
			rand_scale = random.random() * 0.02 + 0.02
			t = Tree(position=(random.randint(-80, 80), 0, random.randint(-80, 80)),
					rotation=(1.57075, random.random() * 6.283, 0),
					scale=(rand_scale, rand_scale, rand_scale))

			diskovery.add_entity(t, "tree" + str(i))

		for i in range(0, 20):
			rand_scale = random.random() * 0.5 + 0.5
			r = Rock(position=(random.randint(-80, 80), 0, random.randint(-80, 80)),
					rotation=(3.14159, random.random() * 6.283, 0),
					scale=(rand_scale, rand_scale, rand_scale))

			diskovery.add_entity(r, "rock" + str(r))

		for i in range(0, 40):
			rand_scale = random.random() * 0.1 + 0.2
			p = Plant(position=(random.randint(-80, 80), 0, random.randint(-80, 80)),
					rotation=(3.14159, random.random() * 6.283, 0),
					scale=(rand_scale, rand_scale, rand_scale))

			diskovery.add_entity(p, "plant" + str(p))

def configs():
	global _entity_configs
	print(_entity_configs)

def edit_scene(filename):

	global _entity_configs

	diskovery.clear_environment()
	diskovery.edit_mode(True)
	_entity_configs.clear()

	diskovery.add_shader("default.vert", "selection.frag", "Selection")
	diskovery.add_shader("basic.vert", "basic.frag", "Basic")
	diskovery.add_shader("default.vert", "terrain_selection.frag", "Terrain")

	diskovery.add_texture("blank.png", "Blank")
	diskovery.add_mesh("cursor.obj", "Cursor", False)
	diskovery.add_texture("cursor.png", "Cursor")
	diskovery.add_entity(Cursor(), "Cursor")

	func_map = { 'Meshes': diskovery.add_mesh,
	 'Textures': diskovery.add_texture,
	 'Shaders': diskovery.add_shader,
	 'Animations': diskovery.add_animation,
	 'Camera': diskovery.set_camera_settings,
	 'LightScenes': diskovery.add_light_scene,
	 'Entities': diskovery.add_entity }

	filled = []

	with open(filename, 'r') as f:
		current = None
		title = f.readline()[:-1]
		current = f.readline()[:-1]

		line = f.readline()[:-1]

		color = 1

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
					if current != 'Shaders' and current != 'Camera':
						exec(cmd)
					line = f.readline()[:-1]
				else:
					class_type = diskovery.get_class(args[1])

					if class_type != diskovery.Terrain:
						rendered_entity_params = {
							'position': 	None,
							'rotation': 	None,
							'scale':		None,
							'mesh_str': 	None,
							'textures_str': None,
							'color':		(color,)
						}

						color += 1

						if 'NotImplementedType' in str(type(class_type.presets)):
							raise NotImplementedError(
								"For extensions of Entity classes to be used with" \
								" DisKovery, they must define a 'presets' dictionary.")

						for name, value in class_type.presets.items():
							if name in rendered_entity_params and rendered_entity_params[name] == None:
								rendered_entity_params[name] = value

						sub_line = f.readline()[:-1]

						class_args = dict(inspect.getmembers(class_type.__init__.__code__))['co_varnames'][1:]
						arg_ptr = 0

						config = {}

						if not issubclass(class_type, RenderedEntity):

							rendered_entity_params['position'] = tuple(
								[float(x) for x in tuple(sub_line.split(' '))]
							)
							config['position'] = rendered_entity_params['position']

							sub_line = f.readline()[:-1]
							rendered_entity_params['rotation'] = tuple(
								[float(x) for x in tuple(sub_line.split(' '))]
							)
							config['rotation'] = rendered_entity_params['rotation']

							rendered_entity_params['scale'] = (0.4, 0.4, 0.4)
							rendered_entity_params['mesh_str'] = "Cube"
							rendered_entity_params['textures_str'] = ["Blank"]
							rendered_entity_params['is_lit'] = (False,)
							rendered_entity_params['name'] = (args[2])

							class_args = dict(inspect.getmembers(class_type.__init__.__code__))['co_varnames'][1:]
							arg_ptr = 2

							sub_line = f.readline()[:-1]
							while sub_line and sub_line[:2] != 'E ':
								param = tuple(sub_line.split(' '))

								if param[0][0] != '\"' and param[0][:2] != '0x':
									param = tuple([float(x) for x in param])

								val = param[0] if len(param) == 1 else param
								if 'str' in str(type(val)) and val[0] == '\"':
									val = val[1:-1]

								config[class_args[arg_ptr]] = val

								arg_ptr += 1
								sub_line = f.readline()[:-1]

							if class_type == Light:
								rendered_entity_params['tint'] = tuple(config['tint']) + (1.0,)

								rendered_entity_params['chi'] = "{}-real".format(args[2])

								diskovery.add_entity(Light(
									config['position'],
									config['rotation'],
									config['tint'],
									config['intensity'],
									config['distance'],
									config['spread'],
									config['scene']
								), "{}-real".format(args[2]))

						else:

							while sub_line and sub_line[:2] != 'E ':
								param = tuple(sub_line.split(' '))


								if param[0][0] != '\"' and param[0][:2] != '0x' and param[0][0] != '[':
									param = tuple([float(x) for x in param])

								elif param[0][0] == '[':
									param = ast.literal_eval(param[0])

								config[class_args[arg_ptr]] = param
								arg_ptr += 1
								sub_line = f.readline()[:-1]

								if None in rendered_entity_params.values():
									next_open = [x for x, y in rendered_entity_params.items() if y == None][0]
									rendered_entity_params[next_open] = param

							rendered_entity_params['name'] = args[2]

						line = sub_line
						_entity_configs[str(args[2])] = config

						cmd = "diskovery.add_entity(SelectableEntity("
						for name, value in rendered_entity_params.items():
							cmd += "{}=".format(name)
							cmd_val = value[0] if len(value) == 1 else value
							if 'str' in str(type(value)):
								cmd += "'{}'".format(cmd_val)
							elif 'list' in str(type(value)):
								cmd += "{}".format(value)
							else:
								cmd += "{}".format(cmd_val)
							cmd += ","

						cmd = cmd[:-1] + "), '{}')".format(args[2])
						print(cmd)
						exec(cmd)
					else:

						class_args = dict(inspect.getmembers(class_type.__init__.__code__))['co_varnames'][1:]
						arg_ptr = 0

						config = {}

						cmd = "diskovery.add_entity(SelectableTerrain("

						sub_line = f.readline()[:-1]
						while sub_line and sub_line[:2] != 'E ':
							param = tuple(sub_line.split(' '))
							if param[0][0] != '\"' and param[0][:2] != '0x':
								param = tuple([float(x) for x in param])

							elif param[0][0] == '\"' and ',' in param[0]:
								param = [x[1:-1] for x in param[0].split(',')]

							config[class_args[arg_ptr]] = param
							arg_ptr += 1

							cmd += str(param[0]) if len(param) == 1 else str(param)
							cmd += ","

							sub_line = f.readline()[:-1]

						cmd += str(color) + ","
						color += 1

						cmd = cmd[:-1] + "), '{}')".format(args[2])
						exec(cmd)
						line = sub_line
						_entity_configs[str(args[2])] = config


					if not line:
						break

			filled.append(current)
			current = line

			line = f.readline()[:-1]

		#diskovery.entity("sir").selected = True


def simplify(attribute):
	if 'vec3' in str(type(attribute)):
		return tuple(attribute)

def arguments(entity_name):
	global _entity_configs
	return _entity_configs[entity_name]

def update_attribute(entity_name, index, value, tuple_bit = -1):
	global _entity_configs

	attrib_name = None 
	for i, val in enumerate(_entity_configs[entity_name].keys()):
		if i == index:
			attrib_name = val

	print(entity_name, attrib_name)

	if tuple_bit != -1:
		v = _entity_configs[entity_name][attrib_name]
		_entity_configs[entity_name][attrib_name] = tuple([value, v[1], v[2]])
		setattr(diskovery.entity(entity_name), attrib_name, glm.vec3(tuple([value, v[1], v[2]])))
	else:
		_entity_configs[entity_name][attrib_name] = value


def update_config(entity, name, attribute):
	global _entity_configs
	if name == None:
		name = entity.name
	_entity_configs[name][attribute] = simplify(getattr(entity, attribute))