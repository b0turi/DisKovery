from enum import Enum
import vk
from ctypes import * 
from xmath import Mat4

class BindingType(Enum):
	UNIFORM_BUFFER = 0

class UniformType(Enum):
	MVP_MATRIX = 0

class MVPMatrix(Structure):
	_fields_ = (
		('model', Mat4),
		('view', Mat4),
		('projection', Mat4)
	)

def get_uniform_size(u_type):
	if u_type == UniformType.MVP_MATRIX:
		return sizeof(MVPMatrix)

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
			max_sets=len(sizes)
		)

		self.dk.CreateDescriptorPool(
			self.dk.device, 
			byref(pool_info), 
			None, 
			byref(self.pool)
		)

	def fill_uniforms(self, index):
		info = vk.DescriptorBufferInfo(
			
		)

	def create_sets(self):
		layouts = (vk.DescriptorSetLayout*self.dk.image_data['count'])()
		self.sets = (vk.DescriptorSet * len(layouts))()
		for layout in layouts:
			layout = self.layout

		alloc_info = vk.DescriptorSetAllocateInfo(
			s_type=vk.STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO,
			descriptor_pool=self.pool,
			descriptor_set_count=len(layouts),
			set_layouts=cast(layouts, POITNER(vk.DescriptorSetLayout))
		)

		self.dk.AllocateDescriptorSets(
			self.dk.device, 
			byref(alloc_info), 
			cast(self.sets, POINTER(vk.DescriptorSet))
		)

		for i in range(0, len(layouts)):



	def __init__(self, dk, definition, layout, uniforms, textures):
		self.dk = dk

		self.pool = vk.DescriptorPool(0)
		self.sets = None
		self.definition = definition
		self.layout = layout

		self.create_pool()

	def set(self, index):
		pass
	def cleanup(self):
		self.dk.DestroyDescriptorPool(self.dk.device, self.pool, None)