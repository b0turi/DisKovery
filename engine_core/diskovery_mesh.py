#!/bin/env/python

import vk
import sys
import glm
import xml.etree.ElementTree as xml
from enum import Enum
from ctypes import *
from diskovery_buffer import Buffer
from diskovery_entity_manager import EntityManager

class VertexLoader:
	def __init__(self, index, position):
		self.index = index
		self.position = position
		self.tex_ind = None
		self.norm_ind = None
		self.duplicate = None

class Vertex(Structure):
	_fields_ = (
		('position', (c_float*3)), 
		('color', (c_float*3)),
		('tex_coord', (c_float*2)),
		('normal', (c_float*3)),
		('joint_ids', (c_uint*3)),
		('weights', (c_float*3))
	)

	def __str__(self):
		return "Position: {}, {}, {}\nColor: {}, {}, {}\nTexture: {}, {}\nNormal: {}, {}, {}".format(
			self.position[0], self.position[1], self.position[2],
			self.color[0], self.color[1], self.color[2],
			self.tex_coord[0], self.tex_coord[1],
			self.normal[0], self.normal[1], self.normal[2]
		)

class Joint:
	def set_inverse_transform(self, parent_transform):
		transform = parent_transform * self.local_transform
		self.inverse_transform = glm.mat4.inverse(transform)
		for child in self.children:
			child.set_inverse_transform(transform)

	def __init__(self, id, name, local_transform):
		self.children = []
		self.index = index
		self.name = name

		self.local_transform = local_transform

		self.anim_transform = glm.mat4(1.0)
		self.inverse_transform = glm.mat4(1.0)

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

	def process_vertex(self, v_data, ind, tex, norm, n_norm, n_tex):
		vert = int(v_data[0]) - 1
		ind.append(vert)
		current_tex = tex[int(v_data[1]) - 1]
		n_tex[vert] = current_tex
		current_norm = norm[int(v_data[2]) - 1]
		n_norm[vert] = current_norm

	def load_obj(self, file):
		positions = []
		normals = []
		textures = []

		new_norm = None
		new_tex = None

		vertex_list = []
		index_list = []

		with open(file, 'r') as f:
			for line in f:
				contents = line.split(' ')

				if line[0] == '#':
					continue

				if line[:2] == 'v ':
					positions.append(
						(float(contents[1]),
					 	 float(contents[2]), 
						 float(contents[3]))
					)
				elif line[:3] == 'vt ':
					textures.append((float(contents[1]), float(contents[2])))
				elif line[:3] == 'vn ':
					normals.append(
						(float(contents[1]), 
						 float(contents[2]), 
						 float(contents[3]))
					)
				elif line[:2] == 'f ':
					if new_norm is None:
						new_norm = ((c_float*3)*len(positions))()
						new_tex = ((c_float*2)*len(positions))()

					v1 = contents[1].split('/')
					v2 = contents[2].split('/')
					v3 = contents[3].split('/')

					self.process_vertex(
						v1, 
						index_list, 
						textures, 
						normals, 
						new_norm, 
						new_tex
					)
					self.process_vertex(
						v2, 
						index_list, 
						textures, 
						normals, 
						new_norm, 
						new_tex
					)
					self.process_vertex(
						v3, 
						index_list, 
						textures, 
						normals, 
						new_norm, 
						new_tex
					)

		for index, vertex in enumerate(positions):
			v = Vertex()
			v.position = vertex
			v.tex_coord = new_tex[index]
			v.normal = new_norm[index]

			vertex_list.append(v)

		return (vertex_list, index_list)

	def get_child_with_attribute(self, node, tag, attribute, value):
		for child in node:
			if child.tag == tag and child.attrib[attribute] == value:
				return child

	def fill_from_source(self, parent, src_id, lis, corr, dim):
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
				vec = corr * vec
				lis.append((c_float*3)(vec.x, vec.y, vec.z))

			elif dim == 2:
				lis.append((c_float*2)(x, 1 - y))

	def duplicate_handler(self, vll, il, vert, tex_ind, norm_ind):
		if vert.norm_ind == norm_ind and vert.tex_ind == tex_ind:
			index_list.append(pos_ind)
			return
		else:
			if vert.duplicate == None:
				vert.duplicate = VertexLoader(len(vll), vert.position)
				vert.duplicate.tex_ind = tex_ind
				vert.duplicate.norm_ind = norm_ind

				vll.append(vert.duplicate)
				il.append(vert.duplicate.index)
				return
			else:
				self.duplicate_handler(vll, il, vert.duplicate, tex_ind, norm_ind)

	def load_dae(self, file, correction, rigged=False):
		positions = []
		normals = []
		textures = []

		vertex_loader_list = []
		vertex_list = []
		index_list = []

		root = xml.parse(file).getroot()

		if correction:
			corr = glm.rotate(glm.mat4(1.0), glm.radians(90), glm.vec3(1., 0., 0.))
		else:
			corr = glm.mat4(1.0)

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
			vec = corr * vec
			v = VertexLoader(len(vertex_list), (c_float*3)(vec.x, vec.y, vec.z))
			vertex_loader_list.append(v)

		norm_id = self.get_child_with_attribute(
			mesh.find('polylist'),
			'input',
			'semantic',
			'NORMAL'
		).attrib['source'][1:]
		self.fill_from_source(mesh, norm_id, normals, corr, 3)

		tex_id = self.get_child_with_attribute(
			mesh.find('polylist'),
			'input',
			'semantic',
			'TEXCOORD'
		).attrib['source'][1:]
		self.fill_from_source(mesh, tex_id, textures, corr, 2)

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
				self.duplicate_handler(vertex_loader_list, index_list, vert, tex_ind, norm_ind)

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

	def __init__(self, file, parse_type, correction=False):
		if parse_type == ParseType.OBJ_MODEL:
			self.data = self.load_obj(file)

		if parse_type == ParseType.DAE_MODEL:
			self.data = self.load_dae(file, correction)

		if parse_type == ParseType.DAE_RIGGED_MODEL:
			self.data = self.load_dae(file, correction, True)



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

		self.count = len(index_array)

	def cleanup(self):
		self.vertices.cleanup()
		self.indices.cleanup()

class AnimatedMesh(Mesh):
	def __init__(self, dk, file, correction=False):

		if file.split('.')[1] == 'obj':
			raise RuntimeError("`AnimatedMesh` cannot accept data from a .obj file." \
							   " Use a `Mesh` object instead.")

		if file.split('.')[1] == 'dae':
			vertex_list, index_list = Parser(file, ParseType.DAE_RIGGED_MODEL, correction).data

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

		self.count = len(index_array)

class Rig(object):
	def __init__(self, root, joint_count):
		# The root of the Joint hierarchy
		self.root = root
		self.joint_count = joint_count

		self.root.set_inverse_transform(glm.mat4(1.0))

	def fill_joints(self, head, arr):
		arr[head.index] = head.anim_transform
		for child in self.children:
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
		rotation = glm.mix(a.rotation, b.rotation, progression)
		return JointTransform(position, rotation)

	def local_transform(self):
		mat = glm.translate(glm.mat4(1.0), self.position)
		return mat * glm.toMat4(self.rotation)

	def __init__(self, position, rotation):
		# Position and rotation are relative to the parent joint
		self.position = position
		self.rotation = rotation

class KeyFrame(object):
	def __init__(self, timestamp, joint_keys):
		self.timestamp = timestamp
		self.pose = joint_keys

class Animation(object):
	def __init__(self, length, keys):
		self.length = length
		self.keys = keys

class Animator(object):

	def play(self, key):
		self.current_anim = key
		self.anim_time = 0

	def prev_and_next(self):
		for index, frame in enumerate(self.animations[self.current_anim].keys):
			if frame.timestamp > self.anim_time:
				next_frame = frame
				prev_frame = self.animations[self.current_anim].keys[index - 1]
				return (next_frame, prev_frame,)

	def get_prog(self, a, b):
		time = a.timestamp - b.timestamp
		current_time = self.anim_time - b.timestamp
		return current_time / time

	def interpolate(self, prev_frame, next_frame, progression):
		pose = { }
		for name in prev_frame.pose.keys():
			prev_t = prev_frame.pose[name]
			next_t = next_Frame.pose[name]
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

		for child in joint.children:
			self.fill_rig(pose, child, current)

		joint.anim_transform = current * joint.inverse_transform

	def update(self):
		if self.current_anim not in self.animations.keys():
			return

		self.anim_time += EntityManager.get_frame_time()
		if self.anim_time > self.animations[self.current_anim].length:
			sef.anim_time %= self.animations[self.current_anim].length

		pose = self.get_pose()
		self.fill_rig(pose, self.entity.rig, glm.mat4(1.0))


	def __init__(self, entity):
		self.entity = entity

		self.current_anim = None
		self.anim_time = 0

		self.animations = {}