
import vk
import pywavefront
from ctypes import *
from diskovery_buffer import Buffer

class Vertex(Structure):
    _fields_ = (
    	('position', c_float*3), 
    	('color', c_float*3),
    	('tex_coord', c_float*2),
    	('normal', c_float*3)
    )

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

	# (location = 2): Texture Coordinates ((u, v) map for mapping textures to models)
	a[2].binding = 0
	a[2].location = 2
	a[2].format = vk.FORMAT_R32G32_SFLOAT
	a[2].offset = sizeof(c_float) * 6

	# (location = 3): Normal (the normal vector from the vertex, for light calculations)
	a[3].binding = 0
	a[3].location = 3
	a[3].format = vk.FORMAT_R32G32B32_SFLOAT
	a[3].offset = sizeof(c_float) * 8

	return a

class Mesh():
	def __init__(self, dk, file):
		model = pywavefront.Wavefront(file, collect_faces=True)

		vertex_list = []
		index_list = []

		data = model.mesh_list[0].materials[0].vertices
		form = model.mesh_list[0].materials[0].vertex_format

		while len(data) > 0:
			v = Vertex()
			if 'T2F' in form:
				v.tex_coord[0] = data[0]
				v.tex_coord[1] = data[1]
				data = data[2:]

			if 'N3F' in form:
				v.normal[0] = data[0]
				v.normal[1] = data[1]
				v.normal[2] = data[2]
				data = data[3:]

			v.position[0] = data[0]
			v.position[1] = data[1]
			v.position[2] = data[2]

			data = data[3:]

			vertex_list.append(v)

		for face in model.mesh_list[0].faces:
			index_list.append(face[0])
			index_list.append(face[1])
			index_list.append(face[2])

		v_size = sizeof(Vertex) * len(vertex_list)
		i_size = sizeof(c_uint) * len(index_list)

		vertex_array = (Vertex*v_size)()
		index_array = (c_uint*i_size)()

		for index, vertex in enumerate(vertex_list):
			vertex_array[index] = vertex

		for i, index in enumerate(index_list):
			index_array[i] = index

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