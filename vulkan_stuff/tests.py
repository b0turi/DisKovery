from vulkan import *
import ctypes
from diskovery_vulkan import find_memory_type
import diskovery
import pygame
import numpy

diskovery.init()

buff = None
mem = None

def make_buffer(size, usage, properties):
	global buff, mem
	buffer_create = VkBufferCreateInfo(
		sType=VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO,
		size=size,
		usage=usage,
		sharingMode=VK_SHARING_MODE_EXCLUSIVE
	)

	buff = vkCreateBuffer(
		diskovery.device(), 
		buffer_create, 
		None
	)

	mem_req = vkGetBufferMemoryRequirements(
		diskovery.device(), 
		buff
	)

	allocate_info = VkMemoryAllocateInfo(
		sType=VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
		allocationSize=mem_req.size,
		memoryTypeIndex=find_memory_type(
			diskovery.physical_device(),
			mem_req.memoryTypeBits, 
			properties)
	)

	mem = vkAllocateMemory(
		diskovery.device(),
		allocate_info,
		None
	)

	vkBindBufferMemory(diskovery.device(), buff, mem, 0)

surface = pygame.image.load("test.png")
		
extent = VkExtent2D(width=surface.get_width(), height=surface.get_height())
size = extent.width * extent.height * 4
info = bytearray(surface.get_buffer().raw)



make_buffer(
	size,
	VK_BUFFER_USAGE_TRANSFER_SRC_BIT,
	VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | 
	VK_MEMORY_PROPERTY_HOST_COHERENT_BIT
)

if isinstance(info, list):
	info = numpy.array(info)

if isinstance(info, bytearray):
	info = numpy.frombuffer(info, dtype=numpy.uint8)

dst = vkMapMemory(diskovery.device(), mem, 0, size, 0)
ffi.memmove(dst, info, size)
vkUnmapMemory(diskovery.device(), mem)
