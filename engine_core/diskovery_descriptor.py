from enum import Enum
import vk
from ctypes import * 
from xmath import Mat4

class BindingType(Enum):
	UNIFORM_BUFFER = 0

class UniformType(Enum):
	MVP_MATRIX = 0

class MVPMatrix(object):
	def __init__(self):
		self.model = Mat4()
		self.view = Mat4()
		self.projection = Mat4()

	def get_data(self):
		size = sizeof(Mat4)*3

		matrices = (Mat4*3)(
			self.model,
			self.view,
			self.projection
		)

		return matrices

def get_uniform_size(u_type):
	if u_type == UniformType.MVP_MATRIX:
		return vk.DeviceSize(sizeof(Mat4)*3)

def make_set_layout(dk, definition):
	bindings = (vk.DescriptorSetLayoutBinding*len(definition))()

	for index, value in enumerate(definition):
		binding = vk.DescriptorSetLayoutBinding(0)
		binding.binding = index
		binding.descriptor_count = 1

		if definition[index] == BindingType.UNIFORM_BUFFER:
			binding.descriptor_type = vk.DESCRIPTOR_TYPE_UNIFORM_BUFFER
			binding.stage_flags = vk.SHADER_STAGE_VERTEX_BIT

		bindings[index] = binding

	create_info = vk.DescriptorSetLayoutCreateInfo(
		s_type=vk.STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO,
		binding_count=len(definition),
		bindings=cast(bindings, POINTER(vk.DescriptorSetLayoutBinding))
	)

	layout = vk.DescriptorSetLayout(0)
	dk.CreateDescriptorSetLayout(dk.device, byref(create_info), None, byref(layout))
	return layout

class Descriptor(object):

	def create_pool(self):
		sizes = (vk.DescriptorPoolSize*len(self.definition))()

		for index, defn in enumerate(self.definition):
			size = vk.DescriptorPoolSize()

			if defn == BindingType.UNIFORM_BUFFER:
				size.type = vk.DESCRIPTOR_TYPE_UNIFORM_BUFFER

			size.descriptor_count = self.dk.image_data['count']

			sizes[index] = size

		pool_info = vk.DescriptorPoolCreateInfo(
			s_type=vk.STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO,
			pool_size_count=len(sizes),
			pool_sizes=cast(sizes, POINTER(vk.DescriptorPoolSize)),
			max_sets=self.dk.image_data['count']
		)

		self.dk.CreateDescriptorPool(
			self.dk.device, 
			byref(pool_info), 
			None, 
			byref(self.pool)
		)

	def fill_uniforms(self, index):
		infos = (vk.DescriptorBufferInfo*len(self.uniforms))()

		for i, uniform in enumerate(self.uniforms):
			info = vk.DescriptorBufferInfo(
				buffer=uniform.buffer(index),
				offset=0,
				range=get_uniform_size(uniform.u_type)
			)

			infos[i] = info

		return infos

	def create_sets(self):
		layouts = (vk.DescriptorSetLayout*self.dk.image_data['count'])()
		self.sets = (vk.DescriptorSet * len(layouts))()
		for i in range(0, len(layouts)):
			layouts[i] = self.layout

		alloc_info = vk.DescriptorSetAllocateInfo(
			s_type=vk.STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO,
			descriptor_pool=self.pool,
			descriptor_set_count=len(layouts),
			set_layouts=cast(layouts, POINTER(vk.DescriptorSetLayout))
		)

		self.dk.AllocateDescriptorSets(
			self.dk.device, 
			byref(alloc_info), 
			cast(self.sets, POINTER(vk.DescriptorSet))
		)

		for i in range(0, len(layouts)):
			unis = self.fill_uniforms(i)

			u_ptr = 0

			writes = (vk.WriteDescriptorSet*len(self.definition))()
			for j in range(0, len(writes)):
				d_set = vk.WriteDescriptorSet(
					s_type=vk.STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET,
					dst_set=self.sets[i],
					dst_binding=j,
					dst_array_element=0,
					descriptor_count=1
				)

				if self.definition[j] == BindingType.UNIFORM_BUFFER:
					d_set.descriptor_type = vk.DESCRIPTOR_TYPE_UNIFORM_BUFFER
					d_set.buffer_info = pointer(unis[u_ptr])
					u_ptr += 1

				writes[j] = d_set

			self.dk.UpdateDescriptorSets(
				self.dk.device, 
				len(writes),
				cast(writes, POINTER(vk.WriteDescriptorSet)),
				0,
				None
			)


	def __init__(self, dk, definition, layout, uniforms, textures):
		self.dk = dk

		self.pool = vk.DescriptorPool(0)
		self.sets = None
		self.definition = definition
		self.layout = layout
		self.uniforms = uniforms

		self.create_pool()
		self.create_sets()

	def get_set(self, index):
		return self.sets[index]

	def cleanup(self):
		self.dk.DestroyDescriptorPool(self.dk.device, self.pool, None)