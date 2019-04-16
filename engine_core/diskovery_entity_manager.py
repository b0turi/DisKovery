#!/bin/env/python

"""
The :mod:`diskovery_entity_manager` module is similar in its usage to the
:mod:`diskovery_instance` module, in that it contains a large class that
only ever has one instance created, housed inside the :mod:`diskovery`
module. It works in conjunction with the :class:`~diskovery_instance.DkInstance`
object stored in the :mod:`diskovery` module, but is used to handle real-time
event updates and asynchronous events, rather than simply setting up values
to be used elsewhere.

.. warning::

	When an :class:`~diskovery.Entity` of any type is created, if it is not
	added to the EntityManager using :func:`diskovery.add_entity`, an explicit
	call to its `cleanup()` method must be made, or Vulkan errors will occur, as
	the EntityManager calls the `cleanup()` method on all objects inside the
	scene automatically when it is destroyed. Similarly, when any type of
	:class:`~diskovery.Entity` is to be destroyed, if it is before the full scene
	is being destroyed or unloaded, the :func:`diskovery.remove_entity` function
	must be used or else the EntityManager will call `cleanup()` on the Entity
	again, and if it has already been destroyed, this will also cause Vulkan
	errors.

"""

import vk
import time
from ctypes import *
from diskovery_image import Image, image_to_buffer
from diskovery_buffer import Buffer

MAX_FRAMES_IN_FLIGHT = 2
UINT64_MAX = 18446744073709551615

_entities = { }

def update_entities(ind):
	global _entities

	for e in _entities.values():
		e.update(ind)

def cleanup_entities():
	global _entities

	for e in _entities.values():
		e.cleanup()

class Renderer(object):

	def add_color_attachment(self):
		img = Image(
			self.dk,
			self.size,
			self.color_format,
			1,
			self.sample_count,

			vk.IMAGE_USAGE_TRANSIENT_ATTACHMENT_BIT |
			vk.IMAGE_USAGE_COLOR_ATTACHMENT_BIT,

			vk.MEMORY_PROPERTY_DEVICE_LOCAL_BIT,
			vk.IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,
			vk.IMAGE_ASPECT_COLOR_BIT
		)

		self.color_attachments.append(img)

	def create_attachments(self, samples):

		for i in range(0, self.dk.max_color_attachments - 1):
			self.add_color_attachment()

		self.depth_attachment = Image(
			self.dk,
			self.size,
			self.depth_format,
			1,
			self.sample_count,
			vk.IMAGE_USAGE_DEPTH_STENCIL_ATTACHMENT_BIT,
			vk.MEMORY_PROPERTY_DEVICE_LOCAL_BIT,
			vk.IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL,
			vk.IMAGE_ASPECT_DEPTH_BIT
		)

		if samples != vk.SAMPLE_COUNT_1_BIT:
			self.add_color_attachment()
			for i in range(0, self.dk.max_color_attachments - 1):

				img = Image(
					self.dk,
					self.size,
					self.color_format,
					1,
					self.sample_count,

					vk.IMAGE_USAGE_TRANSIENT_ATTACHMENT_BIT |
					vk.IMAGE_USAGE_COLOR_ATTACHMENT_BIT,

					vk.MEMORY_PROPERTY_DEVICE_LOCAL_BIT,
					vk.IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,
					vk.IMAGE_ASPECT_COLOR_BIT
				)

				self.resolve_attachments.append(img)

	def create_frame_buffers(self):
		self.framebuffers = (vk.Framebuffer*self.buffer_count)()

		for index, view in enumerate(self.src):
			if len(self.resolve_attachments) > 0:
				attachments = [x.image_view for x in (self.color_attachments)] + \
					[self.depth_attachment.image_view] + [vk.ImageView(view)] + \
					[x.image_view for x in (self.resolve_attachments)]
			else:
				attachments = [vk.ImageView(view)] + \
					[x.image_view for x in (self.color_attachments)] + \
					[self.depth_attachment.image_view]
			att = (vk.ImageView * len(attachments))(*attachments)

			create_info = vk.FramebufferCreateInfo(
				s_type=vk.STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO,
				render_pass=self.render_pass,
				attachment_count=len(att),
				attachments=cast(att, POINTER(vk.ImageView)),
				width=self.size.width,
				height=self.size.height,
				layers=1
			)

			fb = vk.Framebuffer(0)
			self.dk.CreateFramebuffer(self.dk.device, byref(create_info), None, byref(fb))
			self.framebuffers[index] = fb

	def create_semaphores(self):

		create_info = vk.SemaphoreCreateInfo(
			s_type=vk.STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO,
		)

		for i in range(0, MAX_FRAMES_IN_FLIGHT):
			img = vk.Semaphore(0)
			self.dk.CreateSemaphore(
				self.dk.device,
				byref(create_info),
				None,
				byref(img)
			)
			self.done_rendering[i] = img

	def create_command_buffers(self):
		"""
		Any time a new Entity is added or an Entity is removed from the scene,
		the VkCommandBuffer_ objects need to be updated to reflect the new
		number of draw calls that need to be executed. This method handles
		the creation and recreation of the list of VkCommandBuffer_ objects.
		"""
		global _entities

		# Make sure no other command buffers exist
		self.destroy_command_buffers()

		# Store one VkCommandBuffer_ for each framebuffer
		self.command_buffers = (vk.CommandBuffer*self.buffer_count)()

		alloc_info = vk.CommandBufferAllocateInfo(
			s_type=vk.STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO,
			command_pool=self.dk.pool,
			level=vk.COMMAND_BUFFER_LEVEL_PRIMARY,
			command_buffer_count=self.buffer_count
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

			# TODO: adjust to renderer.size
			render_area.extent = self.size

			# Set the color the screen will reset to when redrawn
			clear_values = (vk.ClearValue*(self.dk.max_color_attachments + 1))()

			for i in range(0, len(clear_values)):
				clear_values[i] = vk.ClearValue()

				if i <  len(clear_values) - 1:
					if i == 0:
						clear_values[i].color = vk.ClearColorValue(
							float32=(c_float*4)(
								self.bg_color[0],
								self.bg_color[1],
								self.bg_color[2],
								1.
							)
						)

					else:
						clear_values[i].color = vk.ClearColorValue(float32=(c_float*4)(0.0,0.0,0.0,1.))

				else:
					clear_values[i].depth_stencil = vk.ClearDepthStencilValue(
						depth=1.,
						stencil=0
					)

			renderpass_info = vk.RenderPassBeginInfo(
				s_type=vk.STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO,
				render_pass=self.render_pass,
				framebuffer=self.framebuffers[index],
				render_area=render_area,
				clear_value_count=len(clear_values),
				clear_values=cast(clear_values, POINTER(vk.ClearValue))
			)

			self.dk.CmdBeginRenderPass(buff, byref(renderpass_info), vk.SUBPASS_CONTENTS_INLINE)

			for entity in _entities.values():

				# Skip standard Entity objects
				if not hasattr(entity, 'mesh') or (hasattr(entity, 'hidden') and entity.hidden):
					continue

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
						0, 1, byref(d_set), 0, None
					)

				self.dk.CmdDrawIndexed(buff, entity.get_mesh().count, 1, 0, 0, 1)

			self.dk.CmdEndRenderPass(buff)

			if self.dk.EndCommandBuffer(buff) != vk.SUCCESS:
				raise RuntimeError("Unable to write command buffer")

	def destroy_command_buffers(self):
		"""
		Calls the internal Vulkan commands necessary to destroy the
		list of VkCommandBuffer_ objects.
		"""
		self.dk.FreeCommandBuffers(
			self.dk.device,
			self.dk.pool,
			len(self.command_buffers),
			cast(self.command_buffers, POINTER(vk.CommandBuffer))
		)

	def refresh(self):

		if hasattr(self, 'src'):
			print("HELLO")
			self.cleanup()

			self.create_attachments(samples)
			self.render_pass = self.dk.get_render_pass(samples)
			self.create_frame_buffers()
			self.create_command_buffers()
			self.create_semaphores()

	def __init__(self, dk, samples, src=None, size=None, bg_color=None):
		self.dk = dk

		self.bg_color = (0.1, 0.2, 0.3) if bg_color is None else bg_color

		self.color_format = dk.color_format
		self.depth_format = dk.depth_format

		self.color_attachments = []
		self.depth_attachment = None
		self.resolve_attachments = []

		self.sample_count = samples

		if src != None:
			self.src = src
			self.size = dk.image_data['extent']
			self.buffer_count = len(src)
		else:
			self.size = size
			self.buffer_count = 1

		self.framebuffers = None
		self.command_buffers = (vk.CommandBuffer * self.buffer_count)()
		self.done_rendering = (vk.Semaphore * MAX_FRAMES_IN_FLIGHT)()

		self.create_attachments(samples)
		self.render_pass = self.dk.get_render_pass(samples, self.dk.max_color_attachments)
		self.create_frame_buffers()
		self.create_command_buffers()
		self.create_semaphores()

	def cleanup(self):

		for color in self.color_attachments:
			color.cleanup()

		self.depth_attachment.cleanup()

		for resolve in self.resolve_attachments:
			resolve.cleanup()

		self.destroy_command_buffers()

		for i in range(0, MAX_FRAMES_IN_FLIGHT):
			self.dk.DestroySemaphore(self.dk.device, self.done_rendering[i], None)

		for fb in self.framebuffers:
			self.dk.DestroyFramebuffer(self.dk.device, fb, None)

class EntityManager(object):
	"""
	The :class:`~diskovery_entity_manager.EntityManager`, as the name
	suggests, stores and manages all Entity objects in the game world at a
	given time. While the :mod:`diskovery` module stores all meshes, textures,
	pipelines, and other related objects that may be used by entities at a given
	time, the :class:`~diskovery_entity_manager.EntityManager` class stores
	Entity objects that hold references to these objects, usually with strings
	that act as keys for the dictionaries in which they are stored. Contained
	within the EntityManager class are:

	- A dictionary of all entities in the game world
	- A list of VkCommandBuffer_ objects to store the draw calls for each entity
	- The :meth:`~diskovery_entity_manager.EntityManager.draw` method that binds
		each entity's buffers, pipeline, and descriptors and executes the Vulkan
		draw call
	- Vulkan OS objects used to ensure the asynchronous events are executed in
		the correct order (VkSemaphore_ and VkFence_ objects)

	**Attributes of the EntityManager class:**

	.. py:attribute:: dk

		A reference to the :class:`~diskovery_instance.DkInstance`
		that stores all the relevant fields for the Vulkan instance
		and handles all Vulkan commands

	.. py:attribute:: _entities

		The dictionary in which all entities in the game world at a given time
		are stored.

	.. py:attribute:: command_buffers

		Stores the list of VkCommandBuffer_ objects used to store the draw calls
		to each framebuffer.

	.. py:attribute:: image_available

		A list of VkSemaphore_ objects that signal when a given framebuffer is
		available to be drawn on.

	.. py:attribute:: render_finished

		A list of VkSemaphore_ objects that signal when a given framebuffer has
		completed all of its draw calls and is ready to be presented.

	.. py:attribute:: in_flight_fences

		A list of VkFence_ objects that are used in conjunction with the
		semaphores to wait until a given framebuffer is available to have its
		draw calls executed, and then signal when those operations are done.

	.. py:attribute:: current_frame

		A value that gives the current place within the list of frames in flight
		where the next available framebuffer can be rendered to. This value is
		updated with each draw call and increases incrementally.

	.. py:attribute:: bg_color

		A tuple that stores the normalized RGB values that define the color the
		game screen will be filled with when each new frame begins. The default
		is black, but the user can define another color if they choose. This
		is typically done by passing a 'bg_color' value in the config dictionary
		when initializing DisKovery, where a tuple of 3 values can be passed.
	if hasattr(entity, 'mesh'):


	"""
	def get_frame_time(self):
		"""
		Gets the amount of time, in nanoseconds, between two given frames being
		completed. This difference is used when calculating the interpolation
		of animated models.

		:returns: the amount of time it takes to render one frame
		"""
		return (self.TIME_VAL - self.LAST_TIME_VAL)

	def add_entity(self, entity, name):
		"""
		Adds an entity to the dictionary of entities. If the entity
		given is a :class:`~diskovery.RenderedEntity`, this method
		will also refresh the command buffers to include the draw
		calls for this new entity.

		:param entity: The :class:`~diskovery.Entity` to be added
		:param name: A name to address the entity with
		"""
		global _entities

		_entities[name] = entity

		self.refresh()

	def remove_entity(self, name):
		"""
		Given the name by which an :class:`~diskovery.Entity` in the
		dictionary of entities is addressed, remove it from the
		dictionary, and if it was a :class:`~diskovery.RenderedEntity`,
		update the command buffers to not include this Entity in the
		draw calls.

		:param name: The name of the entity to remove
		"""
		global _entities

		ent = _entities[name]
		ent.cleanup()

		self.refresh()

	def refresh(self):
		for renderer in self.renderers:
			renderer.create_command_buffers()

	def create_sync_objects(self):
		"""
		Each frame will need objects to signal when it is done rendering
		and when it's ready to be filled again, and these semaphores and
		fences act as the objects that signal these. An internal value
		for the maximum number of frames that can be processed at once
		(MAX_FRAMES_IN_FLIGHT) will determine how many of each of these
		objects are created.
		"""

		# All semaphores and fences use the same creation info
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
			self.renders_finished[i] = ren

			f = vk.Fence(0)
			self.dk.CreateFence(
				self.dk.device,
				byref(fcreate_info),
				None,
				byref(f)
			)
			self.in_flight_fences[i] = f

	def draw(self):
		"""
		Performs the necessary Vulkan operations to submit the images
		stored in the framebuffers to the presentation queue to be
		displayed on the surface.
		"""
		self.LAST_TIME_VAL = self.TIME_VAL
		self.TIME_VAL = time.perf_counter()

		fence = vk.Fence(self.in_flight_fences[self.current_frame])
		image = vk.Semaphore(self.image_available[self.current_frame])
		render = vk.Semaphore(self.renders_finished[self.current_frame])

		if self.quitting:
			return

		self.dk.WaitForFences(
			self.dk.device,
			1,
			pointer(fence),
			vk.TRUE,
			UINT64_MAX
		)

		next_image = c_uint(0)
		result = self.dk.AcquireNextImageKHR(
			self.dk.device,
			self.dk.swap_chain,
			c_ulonglong(-1),
			image,
			vk.Fence(0),
			byref(next_image)
		)

		# if result == vk.ERROR_OUT_OF_DATE_KHR:
		# 	self.dk.refresh()
		# 	for r in self.renderers:
		# 		r.refresh()
		# 	return
		# elif result != vk.SUCCESS and result != vk.SUBOPTIMAL_KHR:
		# 	raise RuntimeError("Failed to acquire next swap chain image")

		image_index = next_image.value

		update_entities(image_index)

		self.dk.ResetFences(
			self.dk.device,
			1,
			pointer(fence)
		)

		for i, renderer in enumerate(self.renderers):
			is_first = (i == 0)
			is_last = (i == (len(self.renderers) - 1))

			if renderer.buffer_count > 1:
				cmd = vk.CommandBuffer(renderer.command_buffers[image_index])
			else:
				cmd = vk.CommandBuffer(renderer.command_buffers[0])

			submit_info = vk.SubmitInfo(
				s_type=vk.STRUCTURE_TYPE_SUBMIT_INFO,
				wait_semaphore_count=1,
				signal_semaphore_count=1,
				command_buffer_count=1,
				command_buffers=pointer(cmd),
				wait_dst_stage_mask=pointer(c_uint(vk.PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT))
			)

			if is_first:
				submit_info.wait_semaphores = pointer(image)
			else:
				sem = vk.Semaphore(self.renderers[i - 1].done_rendering[self.current_frame])
				submit_info.wait_semaphores = pointer(sem)

			if is_last:
				submit_info.signal_semaphores = pointer(render)
			else:
				sem = vk.Semaphore(renderer.done_rendering[self.current_frame])
				submit_info.signal_semaphores = pointer(sem)


			if is_last:
				self.dk.QueueSubmit(self.dk.graphics['queue'], 1, byref(submit_info), fence)
			else:
				self.dk.QueueSubmit(self.dk.graphics['queue'], 1, byref(submit_info), vk.Fence(0))

		present_info = vk.PresentInfoKHR(
			s_type=vk.STRUCTURE_TYPE_PRESENT_INFO_KHR,
			swapchain_count=1,
			swapchains=pointer(self.dk.swap_chain),
			image_indices=pointer(next_image),
			wait_semaphore_count=1,
			wait_semaphores=pointer(render)
		)

		result = self.dk.QueuePresentKHR(self.dk.present['queue'], byref(present_info))

		# if result == vk.ERROR_OUT_OF_DATE_KHR or result == vk.SUBOPTIMAL_KHR or self.dk.frame_resized:
		# 	self.dk.frame_resized = False
		# 	self.dk.refresh()
		# 	for r in self.renderers:
		# 		r.refresh()
		# elif result != vk.SUCCESS:
		# 	raise RuntimeError("Unable to present swap chain image")

		self.current_frame = (self.current_frame + 1) % MAX_FRAMES_IN_FLIGHT

	def __init__(self, dk):
		self.dk = dk

		self.renderers = []

		self.image_available = (vk.Semaphore*MAX_FRAMES_IN_FLIGHT)()
		self.renders_finished = (vk.Semaphore*MAX_FRAMES_IN_FLIGHT)()
		self.in_flight_fences = (vk.Fence*MAX_FRAMES_IN_FLIGHT)()

		self.current_frame = 0
		self.quitting = False

		self.TIME_VAL = time.perf_counter()

		self.create_sync_objects()

	def entities(self):
		global _entities
		return _entities

	def add_renderer(self, renderer):
		self.renderers.insert(0, renderer)


	def get_image(self, renderer_ind = 0, col_att = 0, region = None):
		img = self.renderers[0].resolve_attachments[0].image

		if region == None:
			sub = vk.ImageSubresourceLayers(
				aspect_mask=vk.IMAGE_ASPECT_COLOR_BIT,
				mip_level=0,
				base_array_layer=0,
				layer_count=1,
			)

			region = vk.BufferImageCopy(
				image_subresource=sub,
				image_offset=vk.Offset3D(0, 0, 0),
				image_extent=vk.Extent3D(self.dk.image_data['extent'].width,
										 self.dk.image_data['extent'].height, 1)
			)

		size = 4

		buff = Buffer(self.dk, size, None, None, False)
		image_to_buffer(self.dk, img, buff.buffer, region)

		dst = (c_ubyte * size)()
		src = vk.c_void_p(0)

		self.dk.MapMemory(
			self.dk.device,
			buff.memory,
			0,
			buff.mem_req.size,
			0,
			byref(src)
		)
		memmove(dst, src, size)
		self.dk.UnmapMemory(self.dk.device, buff.memory)

		buff.cleanup()

		return dst

	def cleanup(self):
		"""
		Handles necessary Destroy methods for all the Vulkan components
		contained inside the :class:`~diskovery_entity_manager.EntityManager`
		"""
		self.dk.DeviceWaitIdle(self.dk.device)
		for r in self.renderers:
			r.cleanup()

		for i in range(0, MAX_FRAMES_IN_FLIGHT):
			self.dk.DestroySemaphore(self.dk.device, self.image_available[i], None)
			self.dk.DestroySemaphore(self.dk.device, self.renders_finished[i], None)
			self.dk.DestroyFence(self.dk.device, self.in_flight_fences[i], None)

		cleanup_entities()

	def deselect(self):
		global _entities

		_entities["Cursor"].hide()

		for ent in _entities.values():
			ent.selected = False

	def entity_by_color(self, color):
		global _entities
		for ent in _entities.values():
			if hasattr(ent, 'color') and ent.color == tuple(x/255 for x in color):
				return ent

	def is_selected(self):
		global _entities
		for ent in _entities.values():
			if hasattr(ent, 'selected') and ent.selected:
				return True

		return False

	def get_selected(self):
		global _entities
		for name, ent in _entities.items():
			if hasattr(ent, 'selected') and ent.selected:
				return (name, ent)

		return (None, None)