from diskovery_window import DiskoveryWindow
from diskovery_device_manager import DeviceManager
from diskovery_swap_chain import SwapChain
from diskovery_vulkan import *
from diskovery_pipeline import Pipeline
from diskovery_command_buffer import *
from diskovery_sync_objects import SyncObjects
from vulkan import *

class DisKovery():
	def __init__(self):
		self.window = None
		self.device_manager = None
		self.swap_chain = None
		self.render_pass = None
		self.pipeline = None
		self.framebuffers = None
		self.command_pool = None
		self.command_buffers = None
		self.sync = None

		self.current_frame = 0

		self.window = DiskoveryWindow(800, 600)
		self.device_manager = DeviceManager(self.window)
		self.swap_chain = SwapChain(self.window, self.device_manager)

		self.extent = self.swap_chain.extent

		self.render_pass = make_render_pass(
			self.swap_chain.surface_format, 
			self.device_manager.logical_device
		)

		self.framebuffers = make_frame_buffers(
			self.swap_chain.image_views, 
			self.render_pass, 
			self.extent, 
			self.device_manager.logical_device
		)

		self.command_pool = make_command_pool(
			self.device_manager.logical_device, 
			self.device_manager.graphics_queue["index"]
		)

		self.pipeline = Pipeline(
			self.device_manager.logical_device, 
			self.render_pass, 
			self.extent
		)

		self.command_buffers = CommandBuffer(
			self.command_pool, 
			self.device_manager.logical_device,
			self.framebuffers, 
			self.render_pass, 
			self.extent, 
			self.pipeline.pipeline_ref
		)

		self.sync = SyncObjects(
			self.device_manager.logical_device, 
			self.command_buffers.buffers, 
			self.swap_chain.swap_chain_ref
		)

	def cleanup(self): 
		self.sync.cleanup()
		self.command_buffers.cleanup()
		destroy_frame_buffers(self.device_manager.logical_device, self.framebuffers)
		destroy_command_pool(self.device_manager.logical_device, self.command_pool)
		self.pipeline.cleanup()
		destroy_render_pass(self.device_manager.logical_device, self.render_pass)
		self.swap_chain.cleanup()
		self.device_manager.cleanup()
		self.window.cleanup()

	def draw_frame(self):
		try:
		    image_index = get_vulkan_command(self.window.instance, "vkAcquireNextImageKHR")(
		    	self.device_manager.logical_device, 
		    	self.swap_chain.swap_chain_ref, 
		    	UINT64_MAX, 
		       	self.sync.image_available, 
		       	None
		    )
		except VkNotReady:
		    print('not ready')
		    return

		self.sync.submit_create.pCommandBuffers[0] = self.command_buffers.buffers[image_index]

		vkQueueSubmit(self.device_manager.graphics_queue["queue"], 
			1, 
			self.sync.submit_list, 
			None
		)

		self.sync.present_create.pImageIndices[0] = image_index
		get_vulkan_command(self.window.instance, "vkQueuePresentKHR")(
			self.device_manager.present_queue["queue"], 
			self.sync.present_create
		)

	def refresh(self):
		wid = hei = 0
		while wid == 0 or hei == 0:
			wid, hei = pygame.display.get_surface().get_size()

		vkDeviceWaitIdle(self.device_manager.logical_device)

		self.command_buffers.cleanup()




