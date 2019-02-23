from diskovery_vulkan import get_uniform_size
from diskovery_buffer import Buffer
from numpy import array
from vulkan import *
import diskovery

class UniformBuffer():
	def __init__(self, uniform_type):
		self.size = get_uniform_size(uniform_type)

		self.buffers = []
		for i in range(0, diskovery.num_back_buffers()):
			self.buffers.append(Buffer(self.size))

		self.uniform_type = uniform_type

	def update(self, data, index):
		dst = vkMapMemory(diskovery.device(), self.buffers[index].memory, 0, self.size, 0)
		ffi.memmove(dst, array(data), self.size)
		vkUnmapMemory(diskovery.device(), self.buffers[index].memory)

	def get_buffer(self, index):
		return self.buffers[index].buffer

	def cleanup(self):
		for buff in self.buffers:
			buff.cleanup()