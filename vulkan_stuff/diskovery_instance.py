from diskovery_window import DiskoveryWindow
from diskovery_device_manager import DeviceManager
from diskovery_swap_chain import SwapChain
from diskovery_vulkan import *
from diskovery_image import Image
from vulkan import *

class DisKovery():
	def __init__(self):

		self.window = DiskoveryWindow(800, 600)
		self.device_manager = DeviceManager(self.window)
		self.swap_chain = SwapChain(self.window, self.device_manager)

		self.extent = self.swap_chain.extent

		self.command_pool = make_command_pool(
			self.device_manager.logical_device, 
			self.device_manager.graphics_queue["index"]
		)

	def fill(self):

		# TODO: for antialiasing
		self.color_attachment = Image(
			self.extent,
			self.swap_chain.image_format,
			1,
			VK_SAMPLE_COUNT_1_BIT,
			VK_IMAGE_USAGE_TRANSIENT_ATTACHMENT_BIT | VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT,
			VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT,
			VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,
			VK_IMAGE_ASPECT_COLOR_BIT
		)

		self.depth_attachment = Image(
			self.extent,
			self.swap_chain.depth_format,
			1,
			VK_SAMPLE_COUNT_1_BIT,
			VK_IMAGE_USAGE_DEPTH_STENCIL_ATTACHMENT_BIT,
			VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT,
			VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL,
			VK_IMAGE_ASPECT_DEPTH_BIT
		)

		self.render_pass = make_render_pass(
			self.swap_chain.image_format, 
			self.swap_chain.depth_format,
			self.device_manager.logical_device
		)

		self.framebuffers = make_frame_buffers(
			self.color_attachment.image_view,
			self.depth_attachment.image_view,
			self.swap_chain.image_views, 
			self.render_pass, 
			self.extent, 
			self.device_manager.logical_device
		)

	def cleanup(self): 
		destroy_frame_buffers(self.device_manager.logical_device, self.framebuffers)
		destroy_command_pool(self.device_manager.logical_device, self.command_pool)
		destroy_render_pass(self.device_manager.logical_device, self.render_pass)

		self.color_attachment.cleanup()
		self.depth_attachment.cleanup()

		self.swap_chain.cleanup()
		self.device_manager.cleanup()
		self.window.cleanup()

	def start_command(self):
		allocate_info = VkCommandBufferAllocateInfo(
			sType=VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO,
			level=VK_COMMAND_BUFFER_LEVEL_PRIMARY,
			commandPool=self.command_pool,
			commandBufferCount=1
		)

		buff = vkAllocateCommandBuffers(self.device_manager.logical_device, allocate_info)

		begin_info = VkCommandBufferBeginInfo(
			sType=VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO,
			flags=VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT
		)

		vkBeginCommandBuffer(buff[0], begin_info)
		return buff[0]

	def end_command(self, buff):
		vkEndCommandBuffer(buff)

		submit_info = VkSubmitInfo(
			sType=VK_STRUCTURE_TYPE_SUBMIT_INFO,
			commandBufferCount=1,
			pCommandBuffers=[buff]
		)

		vkQueueSubmit(self.device_manager.graphics_queue["queue"], 1, submit_info, VK_NULL_HANDLE)
		vkQueueWaitIdle(self.device_manager.graphics_queue["queue"])

		vkFreeCommandBuffers(self.device_manager.logical_device, self.command_pool, 1, [buff])

	def device(self):
		return self.device_manager.logical_device

	def physical_device(self):
		return self.device_manager.physical_device


