
from vulkan import *
from diskovery_vulkan import find_memory_type
import diskovery
import numpy
import ctypes

class Buffer():
	def __init__(self, size, info=None, usage=None):

		self.buffer = None
		self.memory = None
		self.size = size

		if info != None and usage != None:
			staging_buffer = Buffer(size, info)
			self.make_buffer(
				size, 
				VK_BUFFER_USAGE_TRANSFER_DST_BIT | usage, 
				VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT
			)
			staging_buffer.cleanup()
		elif info != None and usage == None:
			self.make_buffer(
				size,
				VK_BUFFER_USAGE_TRANSFER_SRC_BIT,
				VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | 
				VK_MEMORY_PROPERTY_HOST_COHERENT_BIT
			)

			if isinstance(info, list):
				info = numpy.array(info)
			
			if isinstance(info, bytearray):
				info = numpy.frombuffer(info, dtype=numpy.uint8)

			dst = vkMapMemory(diskovery.device(), self.memory, 0, size, 0)
			print(dst)
			
			dst = numpy.frombuffer(dst, dtype=numpy.uint8)
			numpy.copyto(dst, info, size)
			vkUnmapMemory(diskovery.device(), self.memory)
		else:
			self.make_buffer(
				size,
				VK_BUFFER_USAGE_UNIFORM_BUFFER_BIT,
				VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT |
				VK_MEMORY_PROPERTY_HOST_COHERENT_BIT
			)


	def make_buffer(self, size, usage, properties):
		buffer_create = VkBufferCreateInfo(
			sType=VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO,
			size=size,
			usage=usage,
			sharingMode=VK_SHARING_MODE_EXCLUSIVE
		)

		self.buffer = vkCreateBuffer(
			diskovery.device(), 
			buffer_create, 
			None
		)

		mem_req = vkGetBufferMemoryRequirements(
			diskovery.device(), 
			self.buffer
		)

		allocate_info = VkMemoryAllocateInfo(
			sType=VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
			allocationSize=mem_req.size,
			memoryTypeIndex=find_memory_type(
				diskovery.physical_device(),
				mem_req.memoryTypeBits, 
				properties)
		)

		self.memory = vkAllocateMemory(
			diskovery.device(),
			allocate_info,
			None
		)

		vkBindBufferMemory(diskovery.device(), self.buffer, self.memory, 0)

	def copy_buffer(self, src, dst, size):
		cmd_buffer = diskovery.start_command()
		copy_region = VkBufferCopy(size=size)
		vkCmdCopyBuffer(cmd_buffer, src, dst, 1, [copy_region])
		diskovery.end_command(cmd_buffer)

	def cleanup(self):
		vkDestroyBuffer(diskovery.device(), self.buffer, None)
		vkFreeMemory(diskovery.device(), self.memory, None)