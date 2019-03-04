#!/bin/env/python

import vk
import time
from ctypes import *

MAX_FRAMES_IN_FLIGHT = 2
UINT64_MAX = 18446744073709551615


class EntityManager(object):

	def get_frame_time(self):
		return self.TIME_VAL - self.LAST_TIME_VAL  

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
				vk.ClearValue(color=vk.ClearColorValue(float32=(c_float*4)(0., 1., 0., 1.))),
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

				offset = c_ulonglong(0)
				self.dk.CmdBindVertexBuffers(
					buff, 
					0, 
					1, 
					byref(entity.get_mesh().vertices.buffer),
					byref(offset)
				)

				self.dk.CmdBindIndexBuffer(
					buff,
					entity.get_mesh().indices.buffer,
					0,
					vk.INDEX_TYPE_UINT32
				)

				if hasattr(entity, "descriptor"):
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

				self.dk.CmdDrawIndexed(buff, entity.get_mesh().count, 1, 0, 0, 1)

			self.dk.CmdEndRenderPass(buff)
			if self.dk.EndCommandBuffer(buff) != vk.SUCCESS:
				raise RuntimeError("Unable to write command buffer")

	def create_semaphores(self):
		create_info = vk.SemaphoreCreateInfo(
			s_type=vk.STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO,
		)

		fcreate_info = vk.FenceCreateInfo(
			s_type=vk.STRUCTURE_TYPE_FENCE_CREATE_INFO,
			flags=vk.FENCE_CREATE_SIGNALED_BIT
		)

		for i in range(0, MAX_FRAMES_IN_FLIGHT):

			img = vk.Semaphore(0)
			self.dk.CreateSemaphore(
				self.dk.device, 
				byref(create_info), 
				None, 
				byref(img)
			)
			self.image_available[i] = img

			ren = vk.Semaphore(0)
			self.dk.CreateSemaphore(
				self.dk.device, 
				byref(create_info), 
				None, 
				byref(ren)
			)
			self.render_finished[i] = ren

			f = vk.Fence(0)
			self.dk.CreateFence(
				self.dk.device,
				byref(fcreate_info),
				None,
				byref(f)
			)
			self.in_flight_fences[i] = f

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

		self.LAST_TIME_VAL = self.TIME_VAL 
		self.TIME_VAL = time.perf_counter()

		fence = vk.Fence(self.in_flight_fences[self.current_frame])
		image = vk.Semaphore(self.image_available[self.current_frame])
		render = vk.Semaphore(self.render_finished[self.current_frame])

		self.dk.WaitForFences(
			self.dk.device, 
			1, 
			pointer(fence),
			vk.TRUE,
			UINT64_MAX
		)

		self.dk.ResetFences(
			self.dk.device,
			1,
			pointer(fence)
		)

		next_image = c_uint(0)
		self.dk.AcquireNextImageKHR(
			self.dk.device,
			self.dk.swap_chain,
			c_ulonglong(-1),
			image,
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
			wait_semaphores=pointer(image),
			signal_semaphore_count=1,
			signal_semaphores=pointer(render),
			command_buffer_count=1,
			command_buffers=pointer(cmd),
			wait_dst_stage_mask=pointer(c_uint(vk.PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT))
		)

		self.dk.QueueSubmit(self.dk.graphics['queue'], 1, byref(submit_info), fence)

		present_info = vk.PresentInfoKHR(
			s_type=vk.STRUCTURE_TYPE_PRESENT_INFO_KHR,
			swapchain_count=1,
			swapchains=pointer(self.dk.swap_chain),
			image_indices=pointer(next_image),
			wait_semaphore_count=1,
			wait_semaphores=pointer(render)
		)

		self.dk.QueuePresentKHR(self.dk.present['queue'], byref(present_info))

		self.current_frame = (self.current_frame + 1) % MAX_FRAMES_IN_FLIGHT

	def __init__(self, dk):
		self.dk = dk

		self._entities = { }
		self.command_buffers = (vk.CommandBuffer*self.dk.image_data['count'])()

		self.image_available = (vk.Semaphore*MAX_FRAMES_IN_FLIGHT)()
		self.render_finished = (vk.Semaphore*MAX_FRAMES_IN_FLIGHT)()
		self.in_flight_fences = (vk.Fence*MAX_FRAMES_IN_FLIGHT)()

		self.current_frame = 0

		self.TIME_VAL = time.perf_counter()

		self.create_command_buffers()
		self.create_semaphores()

	def cleanup(self):
		for i in range(0, MAX_FRAMES_IN_FLIGHT):
			self.dk.DestroySemaphore(self.dk.device, self.image_available[i], None)
			self.dk.DestroySemaphore(self.dk.device, self.render_finished[i], None)
			self.dk.DestroyFence(self.dk.device, self.in_flight_fences[i], None)
		for entity in self._entities.values():
			entity.cleanup()