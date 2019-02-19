from diskovery_vulkan import BindingType
from vulkan import *

import diskovery

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
