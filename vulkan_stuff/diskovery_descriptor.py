from diskovery_vulkan import BindingType
from vulkan import *

import diskovery

def make_set_layout(definition):
	bindings = []

	for i in range(0, len(definition)):
		b = VkDescriptorSetLayoutBinding()
		b.binding = i
		b.descriptorCount = 1
		
		b.descriptorType = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER if definition[i] == 0 \
					  else VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER

		b.stageFlags = VK_SHADER_STAGE_VERTEX_BIT if definition[i] == 0 \
				  else VK_SHADER_STAGE_FRAGMENT_BIT

		bindings.append(b)

	layout_create = VkDescriptorSetLayoutCreateInfo(
		sType=VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO,
		bindingCount=len(bindings),
		pBindings=bindings
	)

	layout = vkCreateDescriptorSetLayout(diskovery.device(), layout_create, None)
	return layout

class Descriptor:
	def __init__(self, definition, uniforms, textures):
		self.pool = None
		self.sets = []
		self.definition = definition

		self.make_pool()
		self.make_sets(uniforms, textures)

	def make_pool(self):
		sizes = []

		for i in range(0, len(self.definition)):
			size = VkDescriptorPoolSize()

			if self.definition[i] == BindingType.UNIFORM_BUFFER:
				size.type = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER

			if self.definition[i] == BindingType.TEXTURE_SAMPLER:
				size.type = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER

			size.descriptorCount = diskovery.num_back_buffers()
			sizes.append(size)

		pool_create = VkDescriptorPoolCreateInfo(
			sType=VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO,
			poolSizeCount=len(sizes),
			pPoolSizes=sizes,
			maxSets=diskovery.num_back_buffers()
		)

		self.pool = vkCreateDescriptorPool(diskovery.device(), pool_create, None)

	def make_sets(self, uniforms, textures):
		pass

	def cleanup(self):
		pass