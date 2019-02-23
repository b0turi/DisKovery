from diskovery_vulkan import BindingType, get_uniform_size
from vulkan import *

import diskovery
import ctypes

def make_set_layout(definition):
	bindings = []

	for i in range(0, len(definition)):
		b = VkDescriptorSetLayoutBinding()
		b.binding = i
		b.descriptorCount = 1

		if definition[i] == BindingType.UNIFORM_BUFFER:
			b.descriptorType = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER
			b.stageFlags = VK_SHADER_STAGE_VERTEX_BIT
		elif definition[i] == BindingType.TEXTURE_SAMPLER:
			b.descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER
			b.stageFlags = VK_SHADER_STAGE_FRAGMENT_BIT

		bindings.append(b)

	layout_create = VkDescriptorSetLayoutCreateInfo(
		sType=VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO,
		bindingCount=len(bindings),
		pBindings=bindings
	)

	layout = vkCreateDescriptorSetLayout(diskovery.device(), layout_create, None)
	return layout

def fill_uniforms(uniforms, index):
	infos = []

	for uniform in uniforms:
		info = VkDescriptorBufferInfo(
			buffer=uniform.get_buffer(index),
			offset=0,
			range=get_uniform_size(uniform.uniform_type)
		)

		infos.append(info)

	return infos

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
		desc = diskovery.descriptor(self.definition)
		layouts = [desc] * diskovery.num_back_buffers()

		allocate_info = VkDescriptorSetAllocateInfo(
			sType=VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO,
			descriptorPool=self.pool,
			descriptorSetCount=diskovery.num_back_buffers(),
			pSetLayouts=layouts
		)

		self.sets = vkAllocateDescriptorSets(diskovery.device(), allocate_info)

		for i in range(0, diskovery.num_back_buffers()):
			uniform_infos = fill_uniforms(uniforms, i)

			u_ptr = 0
			t_ptr = 0
			writes = []

			for j in range(0, len(self.definition)):
				d_set = VkWriteDescriptorSet()
				d_set.sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET
				d_set.dstSet = self.sets[i]
				d_set.dstBinding = j
				d_set.dstArrayElement = 0

				if self.definition[j] == BindingType.UNIFORM_BUFFER:
					d_set.descriptorType = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER
					d_set.descriptorCount = uniforms[u_ptr].size
					d_set.pBufferInfo = uniform_infos[u_ptr]
					u_ptr += 1
				if self.definition[j] == BindingType.TEXTURE_SAMPLER:
					d_set.descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER
					d_set.descriptorCount = 1

					image_info = VkDescriptorImageInfo(
						imageLayout=VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
						imageView=diskovery.texture(textures[t_ptr]).image_view,
						sampler=diskovery.texture_sampler(1)
					)

					d_set.pImageInfo = ctypes.pointer(image_info)

				writes.append(d_set)

			vkUpdateDescriptorSets(diskovery.device(), len(writes), writes, 0, None)




	def cleanup(self):
		pass