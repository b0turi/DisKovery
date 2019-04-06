#!/bin/env/python

"""
The :mod:`~diskovery_buffer` module handles all operations involving VkBuffer_
and VkDeviceMemory_ objects. These two objects, in conjunction, define
a region in the device's memory (VRAM if the VkPhysicalDevice_ being used
is a discrete GPU, or RAM if the graphics are being handled by an integrated
graphics card within a CPU). The transferring of data into these regions
is handled by very low level C commands, which are wrapped by the
:class:`~diskovery_buffer.Buffer` class for convenience and readability.

There are two classes defined within the :mod:`~diskovery_buffer` module:

- :class:`~diskovery_buffer.Buffer` - for general purpose buffer and memory operations
- :class:`~diskovery_buffer.UniformBuffer` - for passing data to a :class:`~diskovery_descriptor.Descriptor` with an array of :class:`~diskovery_buffer.Buffer` objects

.. _VkBuffer: https://www.khronos.org/registry/vulkan/specs/1.1-extensions/man/html/VkBuffer.html
.. _VkDeviceMemory: https://www.khronos.org/registry/vulkan/specs/1.1-extensions/man/html/VkDeviceMemory.html
.. _VkPhysicalDevice: https://www.khronos.org/registry/vulkan/specs/1.1-extensions/man/html/VkPhysicalDevice.html
"""

import vk
from ctypes import *

class Buffer(object):
	"""
	There are 3 distinct uses of the :class:`~diskovery_buffer.Buffer` class,
	which can be differentiated by how many of the optional arguments are
	given in its constructor:

	#.  A Uniform Buffer (only size defined)

		A buffer used for the :class:`~diskovery_buffer.UniformBuffer`
		class stores data relating to a uniform variable defined in
		a Shader. The buffer is passed to a VkDescriptorSet_ in a
		:class:`~diskovery_descriptor.Descriptor` and then bound when
		performing draw calls for the object it relates to.

	#.  A Staging Buffer (size and info defined)

		A staging buffer is used to move data from one place
		to another more efficiently. It handles the actual
		transfer of data from one address to another.

		Staging Buffers' usage flags allow for more efficient copying
		of data from one place to another, making it more efficient
		to load the data into a staging buffer and the copy it
		from the staging buffer to the other buffer using Vulkan's
		vkCmdCopyBuffer_ function.

	#.  A Standard Buffer (size, info, and usage defined)

		A standard buffer is the main use case, and can store any
		data in GPU memory. It is wrapped with an additional
		staging buffer when it is created so that the data is
		more efficiently loaded into the buffer.

		The primary usage of the standard buffer is to store
		vertex and input data for :class:`~diskovery_mesh.Mesh` objects.

	The actual data to be stored in the buffer (passed in the ``info``
	argument) must be passed in a ``ctypes`` array or a ``Structure``.
	Python lists are easily converted to ``ctypes`` arrays:::

		data = [5, 10, 15, 20]
		cdata = (c_int*4)(*data)

	The ``usage`` argument takes usage flags used by Vulkan to
	determine what kind of buffer it should create. The
	VkBufferUsageFlagBits_ enum defines each flag with a different bit
	set to 1 so bitwise operations can be used to combine different usages.

	**Attributes of the Buffer class:**

	.. py:attribute:: dk

		A reference to the :class:`~diskovery_instance.DkInstance`
		that stores all the relevant fields for the Vulkan instance
		and handles all Vulkan commands

	.. py:attribute:: buffer

		Stores the VkBuffer_ handle Vulkan will generate when a new VkBuffer_
		is created

	.. py:attribute:: memory

		Stores the VkDeviceMemory_ handle Vulkan will generate when memory on
		the Vulkan device is allocated

	.. py:attribute:: size

		The size of the buffer to be created, in bytes, stored as an
		integer. If using ``ctypes``, the ``sizeof()`` method would
		give an appropriate value for this field.

	.. _VkDescriptorSet: https://www.khronos.org/registry/vulkan/specs/1.1-extensions/man/html/VkDescriptorSet.html
	.. _vkCmdCopyBuffer: https://www.khronos.org/registry/vulkan/specs/1.1-extensions/man/html/vkCmdCopyBuffer.html
	.. _VkBufferUsageFlagBits: https://www.khronos.org/registry/vulkan/specs/1.1-extensions/man/html/VkBufferUsageFlagBits.html

	"""
	def make_buffer(self, usage, props):
		"""
		Performs the various Vulkan operations required to initialize
		the :attr:`~diskovery_buffer.Buffer.buffer` and allocate the
		:attr:`~diskovery_buffer.Buffer.memory`. The final step
		binds the two together as virtual memory inside the Vulkan device.

		:param usage: Mirrors the ``usage`` attribute described above, the constructor
			will fill the value based on which type of buffer it is:

			- Uniform Buffer: ``VK_BUFFER_USAGE_UNIFORM_BUFFER_BIT``
			- Staging Buffer: ``VK_BUFFER_USAGE_TRANSFER_SRC_BIT``
			- Standard Buffer: ``VK_BUFFER_USAGE_TRANSFER_DST_BIT | usage`` (bitwise OR operation)

		:param props: Similar to ``usage``, has a value passed from the constructor
			based on which type of buffer it is:

			- Uniform Buffer: ``VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT``
			- Staging Buffer: ``VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT``
			- Standard Buffer: ``VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT``

		"""
		buffer_info = vk.BufferCreateInfo(
			s_type=vk.STRUCTURE_TYPE_BUFFER_CREATE_INFO,
			size=self.size,
			usage=usage
		)

		self.dk.CreateBuffer(self.dk.device, byref(buffer_info), None, byref(self.buffer))

		self.mem_req = vk.MemoryRequirements()
		self.dk.GetBufferMemoryRequirements(
			self.dk.device,
			self.buffer,
			byref(self.mem_req)
		)

		alloc_info = vk.MemoryAllocateInfo(
			s_type=vk.STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
			allocation_size=self.mem_req.size,
			memory_type_index=self.dk.get_memory_type(
				self.mem_req.memory_type_bits,
				props
			)
		)

		self.dk.AllocateMemory(self.dk.device, byref(alloc_info), None, byref(self.memory))
		self.dk.BindBufferMemory(self.dk.device, self.buffer, self.memory, 0)

	def copy_buffer(self, src, dst, size):
		"""
		Wraps the vkCmdCopyBuffer_ function with a single use VkCommandBuffer_
		to submit the copy command to the graphics queue. Copies the entire
		contents of one buffer to another, with the offset of both buffers set to ``0``.

		:param src: The VkBuffer_ from which data will be transfered
		:param dst: The VkBuffer_ to which data will be transfered
		:param size: The size of the data to transfer (should be the size of both buffers as well)

		.. _VkCommandBuffer: https://www.khronos.org/registry/vulkan/specs/1.1-extensions/man/html/VkCommandBuffer.html
		"""
		cmd = self.dk.start_command()

		region = vk.BufferCopy(src_offset=0, dst_offset=0, size=0)
		region.size = size
		self.dk.CmdCopyBuffer(cmd, src, dst, 1, byref(region))

		self.dk.end_command(cmd)

	def __init__(self, dk, size, info=None, usage=None, uniform=True):
		self.dk = dk
		# The Vulkan buffer (VkBuffer) that will be referenced elsewhere
		self.buffer = vk.Buffer(0)
		# An allocation of memory (VkDeviceMemory) the buffer will be stored in
		self.memory = vk.DeviceMemory(0)
		# A value that stores the size of the buffer (VkDeviceSize)
		self.size = size


		if info != None and usage != None:
			# Create a standard buffer, wrapped with a staging buffer
			staging_buffer = Buffer(self.dk, size, info)
			self.make_buffer(
				vk.BUFFER_USAGE_TRANSFER_DST_BIT | usage,
				vk.MEMORY_PROPERTY_DEVICE_LOCAL_BIT
			)

			self.copy_buffer(staging_buffer.buffer, self.buffer, size)
			staging_buffer.cleanup()

		elif info != None and usage == None:
			# Create a staging buffer to transfer the data
			self.make_buffer(
				vk.BUFFER_USAGE_TRANSFER_SRC_BIT,
				vk.MEMORY_PROPERTY_HOST_VISIBLE_BIT
			)

			data = vk.c_void_p(0)
			self.dk.MapMemory(
				self.dk.device,
				self.memory,
				0,
				self.mem_req.size,
				0,
				byref(data)
			)
			memmove(data, info, size)
			self.dk.UnmapMemory(self.dk.device, self.memory)
		elif info == None and usage == None and not uniform:
			# Destination buffer for data to be dropped in

			self.make_buffer(
				vk.BUFFER_USAGE_TRANSFER_DST_BIT,
				vk.MEMORY_PROPERTY_HOST_VISIBLE_BIT
			)

		else:
			# Create a Uniform Buffer
			self.make_buffer(
				vk.BUFFER_USAGE_UNIFORM_BUFFER_BIT,
				vk.MEMORY_PROPERTY_HOST_VISIBLE_BIT |
				vk.MEMORY_PROPERTY_HOST_COHERENT_BIT
			)

	def cleanup(self):
		"""
		Handles necessary Destroy methods for all the Vulkan components
		contained inside the :class:`~diskovery_buffer.Buffer`
		"""
		self.dk.DestroyBuffer(self.dk.device, self.buffer, None)
		self.dk.FreeMemory(self.dk.device, self.memory, None)

class UniformBuffer(object):
	"""
	The :class:`~diskovery_buffer.Uniform_Buffer` class is used to store
	data for transfer to the list of VkDescriptorSet_ objects defined in
	a :class:`~diskovery_descriptor.Descriptor`. It is used inside the
	:class:`~diskovery.RenderedEntity` class, with one
	:class:`~diskovery_buffer.UniformBuffer` defined for each uniform
	listed in the definition of that RenderedEntity's :class:`~diskovery_pipeline.Shader`.

	Each :class:`~diskovery_buffer.Uniform_Buffer` holds a list of
	:class:`~diskovery_buffer.Buffer` objects with a length that is
	determined by the number of back buffers the VkPhysicalDevice_ can
	handle, a value that is calculated in the
	:meth:`~diskovery_instance.DkInstance.create_swap_chain` method
	of the :class:`~diskovery_instance.DkInstance` class.

	**Attributes of the UniformBuffer class:**

	.. py:attribute:: dk

		A reference to the :class:`~diskovery_instance.DkInstance`
		that stores all the relevant fields for the Vulkan instance
		and handles all Vulkan commands

	.. py:attribute:: u_type

		The type of uniform the UniformBuffer will store. This type is given
		as a member of the enum :class:`~diskovery_descriptor.UniformType`.

	.. py:attribute:: size

		The size, in bytes, of a uniform with this UniformBuffer's type.
		:func:`~diskovery_descriptor.get_uniform_size` is
		used to retrieve this value.

	.. py:attribute:: buffers

		The list in which :class:`~diskovery_buffer.Buffer` objects are stored.
		The :class:`~diskovery_instance.DkInstance` stores the number of
		back buffers the VkPhysicalDevice_ can handle, and this number is
		used to size this list and append that many :class:`~diskovery_buffer.Buffer`
		objects.

	"""
	def __init__(self, dk, u_type):
		self.dk = dk
		self.u_type = u_type
		self.size = u_type.get_size()

		self.buffers = []

		for i in range(0, self.dk.image_data['count']):
			self.buffers.append(Buffer(self.dk, self.size))

	def update(self, data, index):
		"""
		Takes a given set of data, stored as a ``ctypes`` array or ``Structure``,
		and copies the data into the :class:`~diskovery_buffer.UniformBuffer` object's
		list of buffers at the given index. See the description the
		:class:`~diskovery_buffer.Buffer` class for more info on what can be passed
		to a buffer as data.

		:param data: The data, stored in a ``ctypes`` array or ``Structure``
		:param index: The index of the :class:`~diskovery_buffer.Buffer` the new data will be copied into
		"""
		info = vk.c_void_p(0)
		self.dk.MapMemory(
			self.dk.device,
			self.buffers[index].memory,
			0,
			self.size,
			0,
			byref(info)
		)

		memmove(info, data, self.size)
		self.dk.UnmapMemory(self.dk.device, self.buffers[index].memory)

	def buffer(self, index):
		"""
		Retrieves the VkBuffer_ stored in the :class:`~diskovery_buffer.Buffer`
		at the given index

		:param index: The index of the element in the list of buffers to retrieve
		:returns: The VkBuffer_ stored in the :class:`~diskovery_buffer.Buffer`
			at the given index
		"""
		return self.buffers[index].buffer

	def cleanup(self):
		"""
		Handles necessary Destroy methods for all the Vulkan components
		contained inside the :class:`~diskovery_buffer.Buffer`
		"""
		for buff in self.buffers:
			buff.cleanup()
