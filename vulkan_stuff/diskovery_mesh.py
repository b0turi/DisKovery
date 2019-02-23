#!/bin/env python

import pywavefront
import glm
import diskovery
import ctypes
from sys import getsizeof

from diskovery_buffer import Buffer
from vulkan import *

class Vertex():
	def __init__(self):
		self.position = glm.vec3()
		self.color = glm.vec3()
		self.tex = glm.vec2()
		self.norm = glm.vec3()

	def __eq__(self, other):
		return self.position == other.position and \
		self.color == other.color and \
		self.tex == other.tex and \
		self.norm == other.norm

	def __hash__(self):
		return hash((self.position, self.color, self.tex, self.norm))

	@staticmethod
	def bindings():
		b = VkVertexInputBindingDescription()
		b.binding = 0
		b.stride = getsizeof(Vertex)
		b.inputRate = VK_VERTEX_INPUT_RATE_VERTEX

		return b

	@staticmethod
	def attributes():
		a = [VkVertexInputAttributeDescription(),
			VkVertexInputAttributeDescription(),
			VkVertexInputAttributeDescription(),
			VkVertexInputAttributeDescription()]

		a[0].binding = 0
		a[0].location = 0
		a[0].format = VK_FORMAT_R32G32B32_SFLOAT
		a[0].offset = 0

		a[1].binding = 0
		a[1].location = 1
		a[1].format = VK_FORMAT_R32G32B32_SFLOAT
		a[1].offset = getsizeof(glm.vec3())

		a[2].binding = 0
		a[2].location = 2
		a[2].format = VK_FORMAT_R32G32_SFLOAT
		a[2].offset = getsizeof(glm.vec3()) * 2

		a[3].binding = 0
		a[3].location = 3
		a[3].format = VK_FORMAT_R32G32B32_SFLOAT
		a[3].offset = getsizeof(glm.vec3()) * 2 + getsizeof(glm.vec2())

		return a

class Mesh():
	def __init__(self, file):
		self.model = pywavefront.Wavefront(file, collect_faces=True)

		vertex_array = []
		index_array = []

		data = self.model.mesh_list[0].materials[0].vertices
		form = self.model.mesh_list[0].materials[0].vertex_format

		while len(data) > 0:
			v = Vertex()
			if 'T2F' in form:
				v.tex.x = data[0]
				v.tex.y = data[1]
				data = data[2:]

			if 'N3F' in form:
				v.norm.x = data[0]
				v.norm.y = data[1]
				v.norm.z = data[2]
				data = data[3:]

			v.position.x = data[0]
			v.position.y = data[1]
			v.position.z = data[2]

			data = data[3:]

			vertex_array.append(v)

		for face in self.model.mesh_list[0].faces:
			index_array.append(face[0])
			index_array.append(face[1])
			index_array.append(face[2])

		v_size = getsizeof(vertex_array[0]) * len(vertex_array)
		i_size = getsizeof(index_array[0]) * len(index_array)

		self.vertices = Buffer(
			v_size, 
			vertex_array, 
			VK_BUFFER_USAGE_VERTEX_BUFFER_BIT
		)

		self.indices = Buffer(
			i_size, 
			index_array, 
			VK_BUFFER_USAGE_INDEX_BUFFER_BIT
		)

		self.count = len(index_array)

	def cleanup(self):
		self.vertices.cleanup()
		self.indices.cleanup()