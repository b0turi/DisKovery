import vk
from ctypes import *
from diskovery_descriptor import UniformType, get_uniform_size

class Buffer(object):

	def make_buffer(self, usage, props):
		buffer_info = vk.BufferCreateInfo(
			s_type=vk.STRUCTURE_TYPE_BUFFER_CREATE_INFO,
			next=None,
			flags=0,
			size=self.size,
			usage=usage,
			sharing_mode=vk.SHARING_MODE_EXCLUSIVE,
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
		cmd = self.dk.start_command()

		region = vk.BufferCopy()
		region.size = size
		self.dk.CmdCopyBuffer(cmd, src, dst, 1, byref(region))

		self.dk.end_command(cmd)

	def __init__(self, dk, size, info=None, usage=None):
		self.dk = dk
		# The Vulkan buffer (VkBuffer) that will be referenced elsewhere
		self.buffer = vk.Buffer(0)
		# An allocation of memory (VkDeviceMemory) the buffer will be stored in
		self.memory = vk.DeviceMemory(0)
		# A value that stores the size of the buffer (VkDeviceSize)
		self.size = size

		"""
		There are 3 distinct uses of the Buffer class

			1.  A Staging Buffer (size and info defined)
				A staging buffer is used to move data from one place
				to another more efficiently.

			2.  A Uniform Buffer (only size defined)
				A uniform buffer passes data specifically into a Pipeline
				through a Descriptor set so it can be used in a shader 
				module

			3.	A standard buffer (size, info, and usage defined)
				A standard buffer is the main use case, and can store any
				data in GPU memory. It is wrapped with an additional 
				staging buffer when it is created so that the data is 
				more efficiently loaded into the buffer
		"""
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
				vk.MEMORY_PROPERTY_HOST_VISIBLE_BIT |
				vk.MEMORY_PROPERTY_HOST_COHERENT_BIT
			)

			data = vk.c_void_p(0)
			result = self.dk.MapMemory(
				self.dk.device, 
				self.memory, 
				0, 
				self.mem_req.size, 
				0, 
				byref(data)
			)
			memmove(data, info, size)
			self.dk.UnmapMemory(self.dk.device, self.memory)

		else:
			# Create a Uniform Buffer
			self.make_buffer(
				vk.BUFFER_USAGE_UNIFORM_BUFFER_BIT,
				vk.MEMORY_PROPERTY_HOST_VISIBLE_BIT |
				vk.MEMORY_PROPERTY_HOST_COHERENT_BIT
			)

	def cleanup(self):
		self.dk.DestroyBuffer(self.dk.device, self.buffer, None)
		self.dk.FreeMemory(self.dk.device, self.memory, None)

class UniformBuffer(object):
	def __init__(self, dk, u_type):
		self.dk = dk
		self.u_type = u_type

		self.size = get_uniform_size(self.u_type)

		self.buffers = []

		for i in range(0, self.dk.image_data['count']):
			self.buffers.append(Buffer(self.dk, self.size))

	def update(self, data, index):
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
		return self.buffers[index].buffer

	def cleanup(self):
		for buff in self.buffers:
			buff.cleanup()