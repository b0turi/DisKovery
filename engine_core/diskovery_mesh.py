#!/bin/env/python

import vk
import sys
import glm
import xml.etree.ElementTree as xml
from enum import Enum
from ctypes import *
from diskovery_buffer import Buffer
from diskovery_entity_manager import EntityManager
from diskovery_ubos import JointData, get_matrix_data

def bindings():
	b = (vk.VertexInputBindingDescription*1)()

	b[0].binding = 0
	b[0].stride = sizeof(Vertex)
	b[0].input_rate = vk.VERTEX_INPUT_RATE_VERTEX

	return b

def attributes():
	a = (vk.VertexInputAttributeDescription*4)()

	# The attribute descriptions describe which values go in
	# which locations.

	# (location = 0): Position (position of Vertex relative to 3D model origin)
	a[0].binding = 0
	a[0].location = 0
	# GLSL vectors are handled as colors, each channel (RGBA) maps to (x, y, z, w)
	a[0].format = vk.FORMAT_R32G32B32_SFLOAT
	a[0].offset = 0

	# (location = 1): Color (the tint of a given Vertex for interpolated color)
	a[1].binding = 0
	a[1].location = 1
	a[1].format = vk.FORMAT_R32G32B32_SFLOAT
	a[1].offset = sizeof(c_float) * 3

	# (location = 2): Tex_coord (the (u, v) coordinate for the given vertex in the tex map)
	a[2].binding = 0
	a[2].location = 2
	a[2].format = vk.FORMAT_R32G32_SFLOAT
	a[2].offset = sizeof(c_float) * 6

	# (location = 3): Normal (the normal vector from the vertex, for lighting)
	a[3].binding = 0
	a[3].location = 3
	a[3].format = vk.FORMAT_R32G32B32_SFLOAT
	a[3].offset = sizeof(c_float) * 8

	return a

def animated_attributes():
	a = (vk.VertexInputAttributeDescription*6)(*attributes())

	a[4].binding = 0
	a[4].location = 4
	a[4].format = vk.FORMAT_R32G32B32_SFLOAT
	a[4].offset = sizeof(c_float) * 11

	a[5].binding = 0
	a[5].location = 5
	a[5].format = vk.FORMAT_R32G32B32_SFLOAT
	a[5].offset = sizeof(c_float) * 14

	return a



class ParseType(Enum):
	OBJ_MODEL = 0
	DAE_MODEL = 1
	DAE_RIGGED_MODEL = 2
	DAE_RIG = 3
	DAE_ANIMATIONS = 4

class Parser(object):

	# OBJ Parsing #
	def process_vertex(self, v_data, ind, tex, norm, n_norm, n_tex):
		vert = int(v_data[0]) - 1
		ind.append(vert)
		current_tex = tex[int(v_data[1]) - 1]
		n_tex[vert] = current_tex
		current_norm = norm[int(v_data[2]) - 1]
		n_norm[vert] = current_norm

	def load_obj(self, file):
		normals = []
		textures = []

		new_norm = None
		new_tex = None

		vertex_loader_list = []
		input_list = []
		vertex_list = []
		index_list = []

		with open(file, 'r') as f:
			for line in f:
				contents = line.split(' ')

				if line[0] == '#':
					continue

				if line[:2] == 'v ':
					vertex_loader_list.append(VertexLoader(
						len(vertex_loader_list),
						(c_float * 3)(
							float(contents[1]),
							float(contents[2]),
							float(contents[3])
						)
					))
				elif line[:3] == 'vt ':
					textures.append((float(contents[1]), 1 - float(contents[2])))
				elif line[:3] == 'vn ':
					normals.append(
						(float(contents[1]),
						 float(contents[2]),
						 float(contents[3]))
					)
				elif line[:2] == 'f ':
					for i in range(1, 4):
						for value in contents[i].split('/'):
							input_list.append(int(value) - 1)

		for i in range(0, int(len(input_list)/3)):
			pos_ind = int(input_list[i * 3])
			tex_ind = int(input_list[i * 3 + 1])
			norm_ind = int(input_list[i * 3 + 2])

			vert = vertex_loader_list[pos_ind]
			if vert.norm_ind == None:
				vert.tex_ind = tex_ind
				vert.norm_ind = norm_ind
				index_list.append(pos_ind)
			else:
				self.duplicate_handler(vertex_loader_list, index_list, vert, tex_ind, norm_ind, False)

		for vert in vertex_loader_list:
			if vert.norm_ind == None:
				vert.norm_ind = 0
				vert.tex_ind = 0

			v = Vertex()
			v.position = vert.position
			v.tex_coord = textures[vert.tex_ind]
			v.normal = normals[vert.norm_ind]

			vertex_list.append(v)

		return (vertex_list, index_list)

	# DAE Model Parsing #
	def get_child_with_attribute(self, node, tag, attribute, value):
		for child in node:
			if child.tag == tag and child.attrib[attribute] == value:
				return child

	def fill_from_source(self, parent, src_id, lis, dim, correction):
		src_data_loc = self.get_child_with_attribute(
			parent,
			'source',
			'id',
			src_id
		).find('float_array')

		count = int(src_data_loc.attrib['count'])
		src_data = src_data_loc.text.split(' ')

		for i in range(0, int(count/dim)):
			x = float(src_data[i * dim])
			y = float(src_data[i * dim + 1])

			if dim == 3:
				z = float(src_data[i * dim + 2])
				vec = glm.vec4(x, y, z, 1.0)

				if correction:
					corr = glm.rotate(glm.mat4(1.0), glm.radians(90), glm.vec3(1, 0, 0))
				else:
					corr = glm.mat4(1.0)
				vec = corr * vec

				lis.append((c_float*3)(vec.x, vec.y, vec.z))

			elif dim == 2:
				lis.append((c_float*2)(x, 1 - y))

	def duplicate_handler(self, vll, il, vert, tex_ind, norm_ind, rig):
		if vert.norm_ind == norm_ind and vert.tex_ind == tex_ind:
			il.append(vert.index)
			return
		else:
			if vert.duplicate == None:
				vert.duplicate = VertexLoader(len(vll), vert.position)
				vert.duplicate.tex_ind = tex_ind
				vert.duplicate.norm_ind = norm_ind
				if rig:
					vert.duplicate.joints = vert.joints
					vert.duplicate.weights = vert.weights

				vll.append(vert.duplicate)
				il.append(vert.duplicate.index)
				return
			else:
				self.duplicate_handler(vll, il, vert.duplicate, tex_ind, norm_ind, rig)

	def load_dae(self, file, correction, rigged=False):

		MAX_JOINTS = 3
		root = xml.parse(file).getroot()

		if correction:
			corr = glm.rotate(glm.mat4(1.0), glm.radians(90), glm.vec3(1, 0, 0))
		else:
			corr = glm.mat4(1.0)

		if rigged:
			skin = root.find('library_controllers').find('controller').find('skin')

			joints_id = self.get_child_with_attribute(
				skin.find('vertex_weights'),
				'input',
				'semantic',
				'JOINT'
			).attrib['source'][1:]
			joints_loc = self.get_child_with_attribute(
				skin,
				'source',
				'id',
				joints_id
			).find('Name_array')
			joint_list = joints_loc.text.split(' ')

			weights_id = self.get_child_with_attribute(
				skin.find('vertex_weights'),
				'input',
				'semantic',
				'WEIGHT'
			).attrib['source'][1:]
			weights_loc = self.get_child_with_attribute(
				skin,
				'source',
				'id',
				weights_id
			).find('float_array')

			weights = [float(x) for x in weights_loc.text.split(' ')]

			joint_counts_loc = skin.find('vertex_weights').find('vcount')
			joint_counts = [int(x) for x in joint_counts_loc.text.split(' ')[:-1]]

			p = 0
			skin_values = []
			skin_data = skin.find('vertex_weights').find('v').text.split(' ')
			for count in joint_counts:
				skin = VertexSkin()
				for i in range(0, count):
					joint = skin_data[p]
					weight = weights[int(skin_data[p + 1])]
					p += 2
					skin.add_effect(float(joint), float(weight))
				skin.scale(MAX_JOINTS)
				skin_values.append(skin)

		normals = []
		textures = []

		vertex_loader_list = []
		vertex_list = []
		index_list = []

		mesh = root.find('library_geometries').find('geometry').find('mesh')

		pos_id = mesh.find('vertices').find('input').attrib['source'][1:]
		pos_data_loc = self.get_child_with_attribute(
			mesh,
			'source',
			'id',
			pos_id
		).find('float_array')

		count = int(pos_data_loc.attrib['count'])
		pos_data = pos_data_loc.text.split(' ')

		for i in range(0, int(count/3)):
			x = float(pos_data[i * 3])
			y = float(pos_data[i * 3 + 1])
			z = float(pos_data[i * 3 + 2])
			vec = glm.vec4(x, y, z, 1.0)

			if correction:
				corr = glm.rotate(glm.mat4(1.0), glm.radians(90), glm.vec3(1, 0, 0))
			else:
				corr = glm.mat4(1.0)
			vec = corr * vec

			if rigged:
				v = VertexLoader(
					len(vertex_loader_list),
					(c_float*3)(vec.x, vec.y, vec.z),
					(c_float*MAX_JOINTS)(*skin_values[len(vertex_loader_list)].joints),
					(c_float*MAX_JOINTS)(*skin_values[len(vertex_loader_list)].weights)
				)
			else:
				v = VertexLoader(len(vertex_loader_list), (c_float*3)(vec.x, vec.y, vec.z))
			vertex_loader_list.append(v)

		norm_id = self.get_child_with_attribute(
			mesh.find('polylist'),
			'input',
			'semantic',
			'NORMAL'
		).attrib['source'][1:]
		self.fill_from_source(mesh, norm_id, normals, 3, correction)

		tex_id = self.get_child_with_attribute(
			mesh.find('polylist'),
			'input',
			'semantic',
			'TEXCOORD'
		).attrib['source'][1:]
		self.fill_from_source(mesh, tex_id, textures, 2, correction)

		poly = mesh.find('polylist')
		type_count = len(poly.findall('input'))
		full_data = poly.find('p').text.split(' ')

		new_norm = ((c_float*3)*int(len(full_data)/type_count))()
		new_tex = ((c_float*2)*int(len(full_data)/type_count))()

		for i in range(0, int(len(full_data)/type_count)):
			pos_ind = int(full_data[i * type_count])
			norm_ind = int(full_data[i * type_count + 1])
			tex_ind = int(full_data[i * type_count + 2])

			vert = vertex_loader_list[pos_ind]
			if vert.norm_ind == None:
				vert.tex_ind = tex_ind
				vert.norm_ind = norm_ind
				index_list.append(pos_ind)
			else:
				self.duplicate_handler(vertex_loader_list, index_list, vert, tex_ind, norm_ind, rigged)

		for vert in vertex_loader_list:
			if vert.norm_ind == None:
				vert.norm_ind = 0
				vert.tex_ind = 0

			v = Vertex()
			v.position = vert.position
			v.tex_coord = textures[vert.tex_ind]
			v.normal = normals[vert.norm_ind]

			if rigged:
				v.joint_ids = vert.joints
				v.weights = vert.weights

			vertex_list.append(v)

		if rigged:
			return (vertex_list, index_list, joint_list)
		return (vertex_list, index_list)

	# DAE Rig Parsing #
	def load_joint(self, node, joints, correction, is_root):

		name_id = node.attrib['id']
		index = joints.index(name_id)
		matrix_data = [float(x) for x in node.find('matrix').text.split(' ')]
		matrix = glm.mat4(matrix_data)
		matrix = glm.transpose(matrix)

		if is_root:
			if correction:
				corr = glm.rotate(glm.mat4(1.0), glm.radians(90), glm.vec3(1, 0, 0))
			else:
				corr = glm.mat4(1.0)
			matrix = corr * matrix

		j = Joint(index, name_id, matrix)
		self.joint_count += 1
		for child in node.findall('node'):
			j.children.append(self.load_joint(child, joints, 0, False))

		return j

	def load_rig(self, file, joints, correction):
		root = xml.parse(file).getroot()

		rig = self.get_child_with_attribute(
			root.find('library_visual_scenes').find('visual_scene'),
			'node',
			'id',
			'Armature'
		)

		root_joint = self.load_joint(rig.find('node'), joints, correction, True)
		return Rig(root_joint, self.joint_count)

	# DAE Animation Parsing #
	def load_animations(self, file, correction):
		root = xml.parse(file).getroot()

		anim = root.find('library_animations').find('animation')
		root_joint = self.get_child_with_attribute(
			root.find('library_visual_scenes').find('visual_scene'),
			'node',
			'id',
			'Armature'
		).find('node').attrib['id']

		times = [float(x) for x in anim.find('source').find('float_array').text.split(' ')]
		duration = times[len(times) - 1]

		keyframes = []
		for time in times:
			keyframes.append(KeyFrame(time))

		for joint_node in root.find('library_animations').findall('animation'):

			joint_name_id = joint_node.find('channel').attrib['target'].split('/')[0]

			data_id = self.get_child_with_attribute(
				joint_node.find('sampler'),
				'input',
				'semantic',
				'OUTPUT'
			).attrib['source'][1:]

			transforms = [float(x) for x in self.get_child_with_attribute(
				joint_node,
				'source',
				'id',
				data_id
			).find('float_array').text.split(' ')]

			for i, time in enumerate(times):
				matrix = glm.mat4(transforms[i*16:(i+1)*16])
				matrix = glm.transpose(matrix)

				if joint_name_id == root_joint:
					if correction:
						corr = glm.rotate(glm.mat4(1.0), glm.radians(90), glm.vec3(1, 0, 0))
					else:
						corr = glm.mat4(1.0)
					matrix = corr * matrix

				position = glm.vec3(matrix[3].x, matrix[3].y, matrix[3].z)
				rotation = glm.quat_cast(matrix)
				keyframes[i].pose[joint_name_id] = JointTransform(position, rotation)

		return Animation(duration, keyframes)

	def __init__(self, file, parse_type, correction=False, joints=None):
		if parse_type == ParseType.OBJ_MODEL:
			self.data = self.load_obj(file)

		if parse_type == ParseType.DAE_MODEL:
			self.data = self.load_dae(file, correction)

		if parse_type == ParseType.DAE_RIGGED_MODEL:
			self.data = self.load_dae(file, correction, True)

		if parse_type == ParseType.DAE_RIG:
			self.joint_count = 0
			self.data = self.load_rig(file, joints, correction)

		if parse_type == ParseType.DAE_ANIMATIONS:
			self.data = self.load_animations(file, correction)

class Mesh():
	def __init__(self, dk, file):

		if file.split('.')[1] == 'obj':
			vertex_list, index_list = Parser(file, ParseType.OBJ_MODEL).data

		if file.split('.')[1] == 'dae':
			vertex_list, index_list = Parser(file, ParseType.DAE_MODEL).data

		v_size = sizeof(Vertex) * len(vertex_list)
		i_size = sizeof(c_uint) * len(index_list)

		vertex_array = (Vertex*v_size)(*vertex_list)
		index_array = (c_uint*len(index_list))(*index_list)

		self.vertices = Buffer(
			dk,
			v_size,
			vertex_array,
			vk.BUFFER_USAGE_VERTEX_BUFFER_BIT
		)

		self.indices = Buffer(
			dk,
			i_size,
			index_array,
			vk.BUFFER_USAGE_INDEX_BUFFER_BIT
		)

		self.filename = file
		self.count = len(index_array)

	def cleanup(self):
		self.vertices.cleanup()
		self.indices.cleanup()

class VertexLoader:
	def __init__(self, index, position, joints=None, weights=None):
		self.index = index
		self.position = position
		self.tex_ind = None
		self.norm_ind = None
		self.joints = joints
		self.weights = weights
		self.duplicate = None

class Vertex(Structure):
	_fields_ = (
		('position', (c_float*3)),
		('color', (c_float*3)),
		('tex_coord', (c_float*2)),
		('normal', (c_float*3)),
		('joint_ids', (c_float*3)),
		('weights', (c_float*3))
	)

	def __str__(self):
		return "Position: {}, {}, {}\nColor: {}, {}, {}\nTexture: {}, {}\nNormal: {}, {}, {}".format(
			self.position[0], self.position[1], self.position[2],
			self.color[0], self.color[1], self.color[2],
			self.tex_coord[0], self.tex_coord[1],
			self.normal[0], self.normal[1], self.normal[2]
		)

class VertexSkin:
	def scale(self, num_weights):
		if len(self.joints) > num_weights:
			top = self.weights[:num_weights]
			total = sum(top)

			self.weights = []
			for weight in top:
				self.weights.append(min(weight/total, 1))
			self.joints = self.joints[:num_weights]
		elif len(self.joints) < num_weights:
			while len(self.joints) < num_weights:
				self.joints.append(0)
				self.weights.append(0)

	def add_effect(self, joint, weight):
		for i in range(0, len(self.joints)):
			if weight > self.weights[i]:
				self.weights.insert(i, float(weight))
				self.joints.insert(i, float(joint))
				return

		self.weights.append(weight)
		self.joints.append(joint)

	def __init__(self):
		self.joints = []
		self.weights = []

class Joint:
	def set_inverse_transform(self, parent_transform):
		transform = parent_transform * self.local_transform
		self.inverse_transform = glm.inverse(transform)
		for child in self.children:
			child.set_inverse_transform(transform)

	def __init__(self, index, name, local_transform):
		self.children = []
		self.index = index
		self.name = name

		self.local_transform = local_transform

		self.anim_transform = glm.mat4(1.0)
		self.inverse_transform = glm.mat4(1.0)

class AnimatedMesh(Mesh):
	def __init__(self, dk, file, correction=False, extract_anim=False):

		if file.split('.')[1] == 'obj':
			raise RuntimeError("`AnimatedMesh` cannot accept data from a .obj file." \
							   " Use a `Mesh` object instead.")
		elif file.split('.')[1] == 'dae':
			vertex_list, index_list, joint_list = Parser(file, ParseType.DAE_RIGGED_MODEL, correction).data
			self.rig = Parser(file, ParseType.DAE_RIG, correction, joint_list).data

			if extract_anim:
				self.anim = Parser(file, ParseType.DAE_ANIMATIONS, correction).data
				return
		else:
			raise RuntimeError("Unsupported file type for 3D model and animation data")

		v_size = sizeof(Vertex) * len(vertex_list)
		i_size = sizeof(c_uint) * len(index_list)

		vertex_array = (Vertex*v_size)(*vertex_list)
		index_array = (c_uint*len(index_list))(*index_list)

		self.vertices = Buffer(
			dk,
			v_size,
			vertex_array,
			vk.BUFFER_USAGE_VERTEX_BUFFER_BIT
		)

		self.indices = Buffer(
			dk,
			i_size,
			index_array,
			vk.BUFFER_USAGE_INDEX_BUFFER_BIT
		)

		self.filename = file

		self.count = len(index_array)

class Rig(object):

	@staticmethod
	def _fill_new_joint(joint):
		j = Joint(joint.index, joint.name, joint.local_transform)
		for child in joint.children:
			j.children.append(Rig._fill_new_joint(child))
		return j

	@staticmethod
	def from_template(template):
		count = template.joint_count
		root = Rig._fill_new_joint(template.root)

		return Rig(root, count)

	def __init__(self, root, joint_count):
		# The root of the Joint hierarchy
		self.root = root
		self.joint_count = joint_count

		self.root.set_inverse_transform(glm.mat4(1.0))

	def fill_joints(self, head, arr):
		arr[head.index] = get_matrix_data(head.anim_transform)
		for child in head.children:
			self.fill_joints(child, arr)

	def get_joint_data(self):
		matrix_type = (c_float*4)*4
		joint_data = (matrix_type*self.joint_count)()
		self.fill_joints(self.root, joint_data)
		return joint_data

class JointTransform(object):

	@staticmethod
	def pos_interp(a, b, progression):
		x = a.x + (b.x - a.x) * progression
		y = a.y + (b.y - a.y) * progression
		z = a.z + (b.z - a.z) * progression
		return glm.vec3(x, y, z)

	@staticmethod
	def interpolate(a, b, progression):
		position = JointTransform.pos_interp(a.position, b.position, progression)
		rotation = glm.slerp(a.rotation, b.rotation, progression)
		return JointTransform(position, rotation)

	def local_transform(self):
		mat = glm.translate(glm.mat4(1.0), self.position)
		return mat * glm.mat4_cast(self.rotation)

	def __init__(self, position, rotation):
		# Position and rotation are relative to the parent joint
		self.position = position
		self.rotation = rotation

class KeyFrame(object):
	def __init__(self, timestamp):
		self.timestamp = timestamp
		self.pose = { }

class Animation(object):
	def __init__(self, length, keys):
		self.length = length
		self.keys = keys

		self.filename = None

class Animator(object):

	def play(self, key):
		self.current_anim = key
		self.anim_time = 0

	def prev_and_next(self):
		for index, frame in enumerate(self.anim_dict[self.current_anim].keys):
			if frame.timestamp > self.anim_time:
				next_frame = frame
				prev_frame = self.anim_dict[self.current_anim].keys[index - 1]
				return (next_frame, prev_frame,)

	def get_prog(self, a, b):
		time = a.timestamp - b.timestamp
		current_time = self.anim_time - b.timestamp
		return current_time / time

	def interpolate(self, prev_frame, next_frame, progression):
		pose = { }
		for name in prev_frame.pose.keys():
			prev_t = prev_frame.pose[name]
			next_t = next_frame.pose[name]
			current_t = JointTransform.interpolate(prev_t, next_t, progression)
			pose[name] = current_t.local_transform()
		return pose

	def get_pose(self):
		frames = self.prev_and_next()
		progression = self.get_prog(frames[0], frames[1])
		return self.interpolate(frames[1], frames[0], progression)

	def fill_rig(self, pose, joint, parent_transform):
		current_local = pose[joint.name]
		current = parent_transform * current_local

		joint.anim_transform = current * joint.inverse_transform

		for child in joint.children:
			self.fill_rig(pose, child, current)


	def update(self):
		if self.current_anim not in self.animations:
			return

		self.anim_time += self.em.get_frame_time()
		if self.anim_time > self.anim_dict[self.current_anim].length:
			self.anim_time %= self.anim_dict[self.current_anim].length

		pose = self.get_pose()
		self.fill_rig(pose, self.entity.rig.root, glm.mat4(1.0))

	def __init__(self, em, anim_dict, entity, anims):
		self.em = em
		self.anim_dict = anim_dict
		self.entity = entity

		self.animations = []

		for anim in anims:
			self.animations.append(anim)

		self.current_anim = self.animations[0]
		self.anim_time = 0
