import vk
from ctypes import *

class EntityManager(object):

	def create_command_buffers(self):

		self.destroy_command_buffers()

		self.command_buffers = (vk.CommandBuffer*self.dk.image_data['count'])()

		alloc_info = vk.CommandBufferAllocateInfo(
			s_type=vk.STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO,
			command_pool=self.dk.pool,
			level=vk.COMMAND_BUFFER_LEVEL_PRIMARY,
			command_buffer_count=len(self.command_buffers)
		)

		self.dk.AllocateCommandBuffers(
			self.dk.device,
			byref(alloc_info),
			cast(self.command_buffers, POINTER(vk.CommandBuffer))
		)

		for index, buff in enumerate(self.command_buffers):
			begin_info = vk.CommandBufferBeginInfo(
				s_type=vk.STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO,
				flags=vk.COMMAND_BUFFER_USAGE_SIMULTANEOUS_USE_BIT
			)

			self.dk.BeginCommandBuffer(buff, byref(begin_info))

			render_area = vk.Rect2D()
			render_area.offset = vk.Offset2D(0, 0)
			render_area.extent = self.dk.image_data['extent']

			clear_values = (vk.ClearValue*2)(
				vk.ClearValue(color=vk.ClearColorValue(float32=(c_float*4)(0., 0.4, 0., 1.))),
				vk.ClearValue(depth_stencil=vk.ClearDepthStencilValue(depth=1., stencil=0))	
			)

			renderpass_info = vk.RenderPassBeginInfo(
				s_type=vk.STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO,
				render_pass=self.dk.render_pass,
				framebuffer=self.dk.framebuffers[index],
				render_area=render_area,
				clear_value_count=len(clear_values),
				clear_values=cast(clear_values, POINTER(vk.ClearValue))
			)

			self.dk.CmdBeginRenderPass(buff, byref(renderpass_info), vk.SUBPASS_CONTENTS_INLINE)

			for entity in self._entities.values():
				self.dk.CmdBindPipeline(buff, 
					vk.PIPELINE_BIND_POINT_GRAPHICS, 
					entity.get_pipeline().pipeline_ref
				)

				offset = vk.DeviceSize(0)
				self.dk.CmdBindVertexBuffers(
					buff, 
					0, 
					1, 
					pointer(entity.get_mesh().vertices.buffer),
					pointer(offset)
				)

				self.dk.CmdBindIndexBuffer(
					buff,
					entity.get_mesh().indices.buffer, 
					0,
					vk.INDEX_TYPE_UINT32
				)


				d_set = vk.DescriptorSet(entity.descriptor.get_set(index))
				self.dk.CmdBindDescriptorSets(
					buff,
					vk.PIPELINE_BIND_POINT_GRAPHICS,
					entity.get_pipeline().pipeline_layout,
					0,
					1,
					byref(d_set),
					0,
					None
				)
				self.dk.CmdDrawIndexed(buff, entity.get_mesh().count, 1, 0, 0, 0)

			self.dk.CmdEndRenderPass(buff)
			self.dk.EndCommandBuffer(buff)

	def create_semaphores(self):
		create_info = vk.SemaphoreCreateInfo(
			s_type=vk.STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO,
			next=None,
			flags=0
		)

		self.dk.CreateSemaphore(
			self.dk.device, 
			byref(create_info), 
			None, 
			byref(self.image_available)
		)

		self.dk.CreateSemaphore(
			self.dk.device, 
			byref(create_info), 
			None, 
			byref(self.render_finished)
		)


	def destroy_command_buffers(self):
		self.dk.FreeCommandBuffers(
			self.dk.device,
			self.dk.pool,
			len(self.command_buffers),
			cast(self.command_buffers, POINTER(vk.CommandBuffer))
		)

	def add_entity(self, entity, name):
		self._entities[name] = entity
		self.create_command_buffers()

	def remove_entity(self, name):
		self._entities.remove(name)
		self.create_command_buffers()


	def draw(self):

		self.dk.DeviceWaitIdle(self.dk.device)

		next_image = c_uint(0)
		self.dk.AcquireNextImageKHR(
			self.dk.device,
			self.dk.swap_chain,
			c_ulonglong(-1),
			self.image_available,
			vk.Fence(0),
			byref(next_image)
		)

		image_index = next_image.value

		for entity in self._entities.values():
			entity.update(image_index)

		cmd = vk.CommandBuffer(self.command_buffers[image_index])
		submit_info = vk.SubmitInfo(
			s_type=vk.STRUCTURE_TYPE_SUBMIT_INFO,
			wait_semaphore_count=1,
			wait_semaphores=pointer(self.image_available),
			signal_semaphore_count=1,
			signal_semaphores=pointer(self.render_finished),
			command_buffer_count=1,
			command_buffers=pointer(cmd),
			wait_dst_stage_mask=pointer(c_uint(vk.PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT))
		)

		self.dk.QueueSubmit(self.dk.graphics_q['queue'], 1, byref(submit_info), vk.Fence(0))
		self.dk.QueueWaitIdle(self.dk.graphics_q['queue'])

		present_info = vk.PresentInfoKHR(
			s_type=vk.STRUCTURE_TYPE_PRESENT_INFO_KHR,
			swapchain_count=1,
			swapchains=pointer(self.dk.swap_chain),
			image_indices=pointer(next_image),
			wait_semaphore_count=1,
			wait_semaphores=pointer(self.render_finished)
		)

		self.dk.QueuePresentKHR(self.dk.present_q['queue'], byref(present_info))

	def __init__(self, dk):
		self.dk = dk

		self._entities = { }
		self.command_buffers = (vk.CommandBuffer*self.dk.image_data['count'])()

		self.image_available = vk.Semaphore(0)
		self.render_finished = vk.Semaphore(0)

		self.create_command_buffers()
		self.create_semaphores()

	def cleanup(self):
		self.dk.DestroySemaphore(self.dk.device, self.image_available, None)
		self.dk.DestroySemaphore(self.dk.device, self.render_finished, None)
		for entity in self._entities.values():
			entity.cleanup()