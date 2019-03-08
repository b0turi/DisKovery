#!/bin/env/python

"""
The :mod:`~diskovery_descriptor` module handles the passing of uniform
data into shader programs. A shader written in GLSL will have 
a ``layout()`` tag before every uniform variable it declares,
and those tags can contain information on which bindings and which
sets that uniform is referenced through in the Vulkan code.

For example, a uniform in a vertex shader might contain the model,
view, and projection matrices for a given entity in the world space.
This would be defined in the shader code as::
		
	layout(set = 0, binding = 0) uniform UniformBufferObject {
	    mat4 model;
	    mat4 view;
	    mat4 proj;
	} ubo;

The ``layout()`` tag tells Vulkan that this uniform is expecting 
data in the first binding of the first VkDescriptorSet_ it will
be passed. Each VkDescriptorSet_ has a VkDescriptorSetLayout_ which
defines what kind of binding will be at each location within the set,
how many there will be, and which stages of the shader (vertex or fragment)
can access this binding.

In DisKovery, a dicitionary of VkDescriptorSetLayout_ objects is stored
at the top level in the :mod:`~diskovery` module. Whenever a 
:class:`~diskovery_pipeline.Shader` is added to the environment (via
:func:`~diskovery.add_shader`), its definition is extracted and used to 
create a VkDescriptorSetLayout_ using the 
:func:`~diskovery_descriptor.make_set_layout` function defined below.

:mod:`~diskovery_descriptor` handles the passing of uniform data from
:class:`~diskovery_buffer.UniformBuffer` objects, which each contain a 
list of :class:`~diskovery_buffer.Buffer` objects with the same length
as the number of VkFramebuffer_ objects the pipeline is using.
Because of this, each :class:`~diskovery_descriptor.Descriptor` will 
have a list of VkDescriptorSet_ objects for each binding in its given
VkDescriptorSetLayout_. Each VkDescriptorSet_ must also be stored in a
related VkDescriptorPool_ so Vulkan knows where to pull the descriptor 
set from when the call to vkCmdBindDescriptorSets_ happens during the
draw calls (handled in :class:`~diskovery_entity_manager.EntityManager`).

There are a number of classes stored in :mod:`~diskovery_descriptor` to
increase readability when handling binding and uniform data:

- :class:`~diskovery_descriptor.BindingType` - Shorthand for equivalent VkDescriptorType_ 
- :class:`~diskovery_descriptor.UniformType` - Which user-defined class this uniform 
	buffer will hold the data for
- :class:`~diskovery_descriptor.MVPMatrix` - An object that can fill a 
	:class:`~diskovery_buffer.UniformBuffer` that stores matrix data for rendering 
	a :class:`~diskovery.RenderedEntity`

.. _VkDescriptorSetLayout: https://www.khronos.org/registry/vulkan/specs/1.1-extensions/man/html/VkDescriptorSetLayout.html
.. _VkDescriptorPool: https://www.khronos.org/registry/vulkan/specs/1.1-extensions/man/html/VkDescriptorPool.html
.. _VkDescriptorSet: https://www.khronos.org/registry/vulkan/specs/1.1-extensions/man/html/VkDescriptorSet.html
.. _VkDescriptorType: https://www.khronos.org/registry/vulkan/specs/1.1-extensions/man/html/VkDescriptorType.html
.. _vkCmdBindDescriptorSets: https://www.khronos.org/registry/vulkan/specs/1.1-extensions/man/html/vkCmdBindDescriptorSets.html
.. _VkFramebuffer: https://www.khronos.org/registry/vulkan/specs/1.1-extensions/man/html/VkFramebuffer.html
"""

import vk
import glm
from ctypes import * 
from enum import Enum

class BindingType(Enum):
	"""
	A mapping of all types of bindings for descriptors used in DisKovery.
	
	For now, only Uniform Buffers and Texture Samplers are being used.
	"""
	UNIFORM_BUFFER = 0
	TEXTURE_SAMPLER = 1

def make_set_layout(dk, definition):
	"""
	Given a definition, create a VkDescriptorSetLayout_ using a provided
	:class:`~diskovery_instance.DkInstance`. 

	This function determines the types of values that will be passed in
	VkDescriptorSet_ objects later and defines where each value, or binding,
	is allowed to be referenced by ``layout()`` tags in the shader programs.

	Uniform Buffers can be accessed in the vertex shader, and texture samplers
	can be accessed in the fragment shader. 
	"""
	bindings = (vk.DescriptorSetLayoutBinding*len(definition))()

	for index, value in enumerate(definition):
		binding = vk.DescriptorSetLayoutBinding(0)
		binding.binding = index
		binding.descriptor_count = 1

		if definition[index] == BindingType.UNIFORM_BUFFER:
			binding.descriptor_type = vk.DESCRIPTOR_TYPE_UNIFORM_BUFFER
			binding.stage_flags = vk.SHADER_STAGE_VERTEX_BIT

		if definition[index] == BindingType.TEXTURE_SAMPLER:
			binding.descriptor_type = vk.DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER
			binding.stage_flags = vk.SHADER_STAGE_FRAGMENT_BIT

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
	"""
	The :class:`~diskovery_descriptor.Descriptor` class wraps the creation
	of a VkDescriptorPool_ and an array of VkDescriptorSet_ objects, one for each
	VkFramebuffer_. It stores data passed from a :class:`~diskovery.RenderedEntity`
	and builds Vulkan descriptor objects around this data.

	The implementation of some more advanced graphics programming concepts may 
	require that multiple descriptor sets are bound for each render pass, but for
	simplicity's sake and because the scope of this project does not extend that far,
	:class:`~diskovery_descriptor.Descriptor` objects only store 1 set, mirrored
	in each element of the array of VkDescriptorSet_ objects.

	**Attributes of the Descriptor class:**

	.. py:attribute:: dk

		A reference to the :class:`~diskovery_instance.DkInstance` 
		that stores all the relevant fields for the Vulkan instance
		and handles all Vulkan commands

	.. py:attribute:: pool

		Stores the VkDescriptorPool_ handle needed to create the
		VkDescriptorSet_ array.

	.. py:attribute:: sets

		An array of VkDescriptorSet_ handles, with length equal to the 
		number of VkFramebuffer_ objects the pipeline renders to.

	.. py:attribute:: definition

		A tuple of :class:`~diskovery_descriptor.BindingType` objects 
		that defines the order in which items are bound within a shader
		program.

	.. py:attribute:: layout

		A reference to the VkDescriptorSetLayout_ already created 
		and stored at the top level of the :mod:`diskovery` module.
		It is used to crerate the array of VkDescriptorSet_ objects.

	.. py:attribute:: uniforms

		A list of uniforms that will be used to fill all sets in the
		layout that store a ``DESCRIPTOR_TYPE_UNIFORM_BUFFER`` binding.

	.. py:attribute:: textures

		A list of the textures that will be used to fill all sets
		in the layout that store a ``DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER``
		binding.
	"""
	def create_pool(self):
		"""
		Creates a VkDescriptorPool_ object and stores it in the
		:attr:`~diskovery_descriptor.Descriptor.pool` attribute. 

		Uses the :attr:`~diskovery_descriptor.Descriptor.definition` to
		determine the sizes of each individual pool the VkDescriptorPool_
		will handle.
		"""
		sizes = (vk.DescriptorPoolSize*len(self.definition))()

		for index, defn in enumerate(self.definition):
			size = vk.DescriptorPoolSize()

			if defn == BindingType.UNIFORM_BUFFER:
				size.type = vk.DESCRIPTOR_TYPE_UNIFORM_BUFFER

			if defn == BindingType.TEXTURE_SAMPLER:
				size.type = vk.DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER

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

	def create_sets(self):
		"""
		Creates and fills an array of VkDescriptorSet_ objects of length
		equal to the number of VkFramebuffer_ objects being rendered by
		the pipeline. Retrieves information relevant to each uniform
		and texture passed in and assigns each to a VkWriteDescriptorSet_
		object, an array of which is passed to update the descriptor sets
		after they are allocated within the VkDescriptorPool_

		.. _VkWriteDescriptorSet: https://www.khronos.org/registry/vulkan/specs/1.1-extensions/man/html/VkWriteDescriptorSet.html
		"""
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

			u_ptr = 0
			t_ptr = 0

			writes = (vk.WriteDescriptorSet*len(self.definition))()
			for j in range(0, len(writes)):
				d_set = vk.WriteDescriptorSet(
					s_type=vk.STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET,
					dst_set=self.sets[i],
					dst_binding=j,
					descriptor_count=1
				)

				if self.definition[j] == BindingType.UNIFORM_BUFFER:
					buffer_info = vk.DescriptorBufferInfo(
						buffer=self.uniforms[u_ptr].buffer(i),
						offset=0,
						range=self.uniforms[u_ptr].u_type.get_size()
					)

					d_set.descriptor_type = vk.DESCRIPTOR_TYPE_UNIFORM_BUFFER
					d_set.buffer_info = pointer(buffer_info)
					u_ptr += 1

				if self.definition[j] == BindingType.TEXTURE_SAMPLER:
					image_info = vk.DescriptorImageInfo(
						image_layout=vk.IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
						image_view=self.textures[t_ptr].image_view,
						sampler=self.dk.get_texture_sampler(self.textures[t_ptr].mip)
					)

					d_set.descriptor_type = vk.DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER
					d_set.image_info = pointer(image_info)
					t_ptr += 1

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
		self.textures = textures

		self.create_pool()
		self.create_sets()

	def get_set(self, index):
		"""
		Retrieves the VkDescriptorSet_ at the given index

		:param index: The index from which the VkDescriptorSet_ should be retrieved
		:returns: The VkDescriptorSet_ at the given index
		"""
		return self.sets[index]

	def cleanup(self):
		"""
		Handles necessary Destroy methods for all the Vulkan components 
		contained inside the :class:`~diskovery_buffer.Buffer`
		"""
		self.dk.DestroyDescriptorPool(self.dk.device, self.pool, None)