#!/bin/env/python

import vk, pygame, platform
from ctypes import *
from itertools import chain
from diskovery_image import Image, make_texture_sampler
from diskovery_window import Window

class DkInstance(object):
	def create_instance(self, debug):
		app_info = vk.ApplicationInfo(
			s_type=vk.STRUCTURE_TYPE_APPLICATION_INFO,
			application_name=b'Hello World',
			application_version=vk.MAKE_VERSION(1, 0, 0),
			engine_name=b'DisKovery',
			engine_version=vk.MAKE_VERSION(0, 0, 1),
			api_version=vk.API_VERSION_1_0
		)

		extensions = [b'VK_KHR_surface']
		layers = []
		_layers = None

		if debug:
			extensions.append(b'VK_EXT_debug_report')
			layers.append(c_char_p(b'VK_LAYER_LUNARG_standard_validation'))
			_layers = cast((c_char_p*1)(*layers), POINTER(c_char_p))

		# Add platform specific extensions for displaying a window
		pl = platform.system()
		if pl == 'Windows':
			extensions.append(b'VK_KHR_win32_surface')
		elif pl == 'Darwin': # Mac OS
			extensions.append(b'VK_KHR_xlib_surface')
		elif pl == 'Linux':
			extensions.append(b'VK_KHR_wayland_surface')
		else:
			raise RuntimeError("This platform is not supported!")

		extensions = [c_char_p(x) for x in extensions]
		_extensions = cast((c_char_p*len(extensions))(*extensions), POINTER(c_char_p))

		create_info = vk.InstanceCreateInfo(
			s_type=vk.STRUCTURE_TYPE_INSTANCE_CREATE_INFO,
			appilcation_info=pointer(app_info),
			enabled_layer_count=len(layers),
			enabled_layer_names=_layers,
			enabled_extension_count=len(extensions),
			enabled_extension_names=_extensions
		)

		assert(vk.CreateInstance(byref(create_info), None, byref(self.instance)) == vk.SUCCESS)
		functions = chain(vk.load_functions(self.instance, vk.InstanceFunctions, vk.GetInstanceProcAddr),
						  vk.load_functions(self.instance, vk.PhysicalDeviceFunctions, vk.GetInstanceProcAddr))
		for name, function in functions:
			setattr(self, name, function)

	def create_debugger(self):
		callback_fn = vk.fn_DebugReportCallbackEXT(debug_function)
		create_info = vk.DebugReportCallbackCreateInfoEXT(
			s_type=vk.STRUCTURE_TYPE_DEBUG_REPORT_CREATE_INFO_EXT,
			flags=vk.DEBUG_REPORT_ERROR_BIT_EXT | vk.DEBUG_REPORT_WARNING_BIT_EXT,
			callback=callback_fn
		)

		self.CreateDebugReportCallbackEXT(
			self.instance, 
			byref(create_info), 
			None, 
			byref(self.debugger)
		)

	def pick_gpu(self):
		gpu_count = c_uint(0)
		self.EnumeratePhysicalDevices(self.instance, byref(gpu_count), None)

		buf = (vk.PhysicalDevice*gpu_count.value)()
		self.EnumeratePhysicalDevices(
			self.instance, byref(gpu_count), 
			cast(buf, POINTER(vk.PhysicalDevice))
		)

		self.gpu = vk.PhysicalDevice(buf[0])

		queue_families_count = c_uint(0)
		self.GetPhysicalDeviceQueueFamilyProperties(
			self.gpu,
			byref(queue_families_count),
			None
		)

		queue_families = (vk.QueueFamilyProperties*queue_families_count.value)()
		self.GetPhysicalDeviceQueueFamilyProperties(
			self.gpu,
			byref(queue_families_count),
			cast(queue_families, POINTER(vk.QueueFamilyProperties))
		)

		supported = vk.c_uint(0)
		for index, queue in enumerate(queue_families):
			if queue.queue_count > 0 and queue.queue_flags & vk.QUEUE_GRAPHICS_BIT != 0:
				self.graphics['index'] = index

			self.GetPhysicalDeviceSurfaceSupportKHR(self.gpu, index, self.window.surface, byref(supported))
			if queue.queue_count > 0 and supported.value == 1:
				self.present['index'] = index

			if self.graphics['index'] != None and self.present['index'] != None:
				break

		self.image_data['depth_format'] = self.find_depth_format()

	def create_device(self, debug):

		priorities = (c_float*1)(1.0)
		g_q_create_info = vk.DeviceQueueCreateInfo(
			s_type=vk.STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO,
			queue_family_index=int(self.graphics['index']),
			queue_count=1,
			queue_priorities=priorities
		)

		p_q_create_info = vk.DeviceQueueCreateInfo(
			s_type=vk.STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO,
			queue_family_index=int(self.present['index']),
			queue_count=1,
			queue_priorities=priorities
		)

		queue_create_infos = (vk.DeviceQueueCreateInfo*1)(*(g_q_create_info,))

		extensions = (b'VK_KHR_swapchain',)
		_extensions = cast((c_char_p*len(extensions))(*extensions), POINTER(c_char_p))

		layers = []
		_layers = None

		if debug:
			layers = (b'VK_LAYER_LUNARG_standard_validation',)
			_layers = cast((c_char_p*1)(*layers), POINTER(c_char_p))

		create_info = vk.DeviceCreateInfo(
			s_type=vk.STRUCTURE_TYPE_DEVICE_CREATE_INFO,
			queue_create_info_count=1,
			queue_create_infos=queue_create_infos,
			enabled_layer_count=len(layers),
			enabled_layer_names=_layers,
			enabled_extension_count=len(extensions),
			enabled_extension_names=_extensions
		)

		device = vk.Device(0)
		result = self.CreateDevice(self.gpu, byref(create_info), None, byref(device))
		if result == vk.SUCCESS:
			functions = chain(vk.load_functions(device, vk.QueueFunctions, self.GetDeviceProcAddr),
							  vk.load_functions(device, vk.DeviceFunctions, self.GetDeviceProcAddr),
							  vk.load_functions(device, vk.CommandBufferFunctions, self.GetDeviceProcAddr))

			for name, function in functions:
				setattr(self, name, function)

			self.device = device
		else:
			print(vk.c_int(result))
			raise RuntimeError('Could not create device.')

	def fill_queues(self):
		self.graphics['queue'] = vk.Queue(0)
		self.present['queue'] = vk.Queue(0)

		self.GetDeviceQueue(
			self.device, 
			self.graphics['index'], 
			0, 
			byref(self.graphics['queue'])
		)
		self.GetDeviceQueue(
			self.device, 
			self.present['index'], 
			0, 
			byref(self.present['queue'])
		)

	def create_swap_chain(self):
		capabilities = vk.SurfaceCapabilitiesKHR()
		self.GetPhysicalDeviceSurfaceCapabilitiesKHR(
			self.gpu, 
			self.surface,
			byref(capabilities)
		)

		present_modes_count = c_uint(0)
		self.GetPhysicalDeviceSurfacePresentModesKHR(
			self.gpu,
			self.surface,
			byref(present_modes_count),
			None
		)

		present_modes = (c_uint*present_modes_count.value)()
		self.GetPhysicalDeviceSurfacePresentModesKHR(
			self.gpu,
			self.surface,
			byref(present_modes_count),
			cast(present_modes, POINTER(c_uint))
		)

		if capabilities.current_extent.width == -1:
			width, height = self.window.size()
			extent = vk.Extent2D(width=width, height=height)
		else:
			extent = capabilities.current_extent
			width = extent.width
			height = extent.height

		self.image_data['extent'] = extent

		present_mode = vk.PRESENT_MODE_FIFO_KHR
		if vk.PRESENT_MODE_MAILBOX_KHR in present_modes:
			present_mode = vk.PRESENT_MODE_MAILBOX_KHR
		elif vk.PRESENT_MODE_IMMEDIATE_KHR in present_modes:
			present_mode = vk.PRESENT_MODE_IMMEDIATE_KHR

		self.image_data['count'] = capabilities.min_image_count + 1
		if capabilities.max_image_count > 0 and self.image_data['count'] > capabilities.max_image_count:
			self.image_data['count'] = capabilities.max_image_count

		transform = capabilities.current_transform
		if capabilities.supported_transforms & vk.SURFACE_TRANSFORM_IDENTITY_BIT_KHR != 0:
			transform = vk.SURFACE_TRANSFORM_IDENTITY_BIT_KHR

		format_count = c_uint(0)
		self.GetPhysicalDeviceSurfaceFormatsKHR(
			self.gpu, 
			self.surface, 
			byref(format_count), 
			None
		)

		formats = (vk.SurfaceFormatKHR*format_count.value)()
		self.GetPhysicalDeviceSurfaceFormatsKHR(
			self.gpu,
			self.surface,
			byref(format_count),
			cast(formats, POINTER(vk.SurfaceFormatKHR))
		)

		if format_count == 1 and formats[0].format == vk.FORMAT_UNDEFINED:
			color_format = vk.FORMAT_B8G8R8A8_UNOFRM
		else:
			color_format = formats[0].format

		self.image_data['color_format'] = color_format
		color_space = formats[0].color_space

		queue_family_indices = (c_uint*2)(self.graphics['index'], self.present['index'])

		create_info = vk.SwapchainCreateInfoKHR(
			s_type=vk.STRUCTURE_TYPE_SWAPCHAIN_CREATE_INFO_KHR,
			surface=self.surface,
			min_image_count=self.image_data['count'],
			image_format=self.image_data['color_format'],
			image_color_space=color_space,
			image_extent=self.image_data['extent'],
			image_array_layers=1,
			image_usage=vk.IMAGE_USAGE_COLOR_ATTACHMENT_BIT,
			image_sharing_mode=vk.SHARING_MODE_EXCLUSIVE,
			queue_family_index_count=2,
			queue_family_indices=queue_family_indices,
			pre_transform=transform,
			composite_alpha=vk.COMPOSITE_ALPHA_OPAQUE_BIT_KHR,
			present_mode=present_mode,
			clipped=1,
			old_swapchain=(self.swap_chain or vk.SwapchainKHR(0))
		)

		swap_chain = vk.SwapchainKHR(0)
		result = self.CreateSwapchainKHR(self.device, byref(create_info), None, byref(swap_chain))

		if result == vk.SUCCESS:
			if self.swap_chain is not None:
				self.destroy_swap_chain()
			self.swap_chain = swap_chain
		else:
			raise RuntimeError("Unable to create swapchain")

	def create_sc_views(self):
		image_count = c_uint(0)
		self.GetSwapchainImagesKHR(self.device, self.swap_chain, byref(image_count), None)

		images = (vk.Image * image_count.value)()
		self.GetSwapchainImagesKHR(
			self.device, 
			self.swap_chain, 
			byref(image_count),
			cast(images, POINTER(vk.Image))
		)

		self.sc_image_views = (vk.ImageView*self.image_data['count'])()

		for index, image in enumerate(images):
			components = vk.ComponentMapping(
				r=vk.COMPONENT_SWIZZLE_IDENTITY,
				g=vk.COMPONENT_SWIZZLE_IDENTITY,
				b=vk.COMPONENT_SWIZZLE_IDENTITY,
				a=vk.COMPONENT_SWIZZLE_IDENTITY
			)

			sub_range = vk.ImageSubresourceRange(
				aspect_mask=vk.IMAGE_ASPECT_COLOR_BIT,
				base_mip_level=0,
				level_count=1,
				base_array_layer=0,
				layer_count=1
			)

			create_info = vk.ImageViewCreateInfo(
				s_type=vk.STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO,
				image=image,
				view_type=vk.IMAGE_VIEW_TYPE_2D,
				format=self.image_data['color_format'],
				components=components,
				subresource_range=sub_range
			)

			view = vk.ImageView(0)
			result = self.CreateImageView(self.device, byref(create_info), None, byref(view))
			if result == vk.SUCCESS:
				self.sc_image_views[index] = view
			else:
				raise RuntimeError("Unable to create swapchain image views")

	def create_pipeline_cache(self):
		create_info = vk.PipelineCacheCreateInfo(
			s_type=vk.STRUCTURE_TYPE_PIPELINE_CACHE_CREATE_INFO, 
			next=None,
			flags=0, 
			initial_data_size=0, 
			initial_data=None
		)

		pipeline_cache = vk.PipelineCache(0)
		result = self.CreatePipelineCache(self.device, byref(create_info), None, byref(pipeline_cache))
		if result != vk.SUCCESS:
			raise RuntimeError('Failed to create pipeline cache')

		self.pipeline_cache = pipeline_cache


	def create_pool(self):
		create_info = vk.CommandPoolCreateInfo(
			s_type=vk.STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO,
			flags=vk.COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT,
			queue_family_index=self.graphics['index']
		)

		pool = vk.CommandPool(0)
		result = self.CreateCommandPool(self.device, byref(create_info), None, byref(pool))
		if result == vk.SUCCESS:
			self.pool = pool
		else:
			raise RuntimeError("Unable to create command pool")

	def create_render_pass(self):
		color, depth = vk.AttachmentDescription(), vk.AttachmentDescription()

		color.format = self.image_data['color_format']
		color.samples = vk.SAMPLE_COUNT_1_BIT
		color.load_op = vk.ATTACHMENT_LOAD_OP_CLEAR
		color.store_op = vk.ATTACHMENT_STORE_OP_STORE
		color.stencil_load_op = vk.ATTACHMENT_LOAD_OP_DONT_CARE
		color.stencil_store_op = vk.ATTACHMENT_STORE_OP_DONT_CARE
		color.initial_layout = vk.IMAGE_LAYOUT_UNDEFINED
		color.final_layout = vk.IMAGE_LAYOUT_PRESENT_SRC_KHR

		depth.format = self.image_data['depth_format']
		depth.samples = vk.SAMPLE_COUNT_1_BIT
		depth.load_op = vk.ATTACHMENT_LOAD_OP_CLEAR
		depth.store_op = vk.ATTACHMENT_STORE_OP_DONT_CARE
		depth.stencil_load_op = vk.ATTACHMENT_LOAD_OP_DONT_CARE
		depth.stencil_store_op = vk.ATTACHMENT_STORE_OP_DONT_CARE
		depth.initial_layout = vk.IMAGE_LAYOUT_UNDEFINED
		depth.final_layout = vk.IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL

		color_ref = vk.AttachmentReference( 
			attachment=0, 
			layout=vk.IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL 
		)
		depth_ref = vk.AttachmentReference( 
			attachment=1, 
			layout=vk.IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL 
		)

		subpass = vk.SubpassDescription(
			pipeline_bind_point=vk.PIPELINE_BIND_POINT_GRAPHICS,
			color_attachment_count=1, 
			color_attachments=pointer(color_ref),
			resolve_attachments=None, 
			depth_stencil_attachment=pointer(depth_ref)
		)

		dependency = vk.SubpassDependency(
			src_subpass=vk.SUBPASS_EXTERNAL,
			src_stage_mask=vk.PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
			src_access_mask=0,
			dst_stage_mask=vk.PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
			dst_access_mask=vk.ACCESS_COLOR_ATTACHMENT_READ_BIT | vk.ACCESS_COLOR_ATTACHMENT_WRITE_BIT
		)

		attachments = (vk.AttachmentDescription*2)(color, depth)
		create_info = vk.RenderPassCreateInfo(
			s_type=vk.STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO,
			attachment_count=2,
			attachments=cast(attachments, POINTER(vk.AttachmentDescription)),
			subpass_count=1, 
			subpasses=pointer(subpass), 
			dependency_count=1,
			dependencies=pointer(dependency)
		)

		render_pass = vk.RenderPass(0)
		result = self.CreateRenderPass(self.device, byref(create_info), None, byref(render_pass))
		if result != vk.SUCCESS:
			raise RuntimeError("Couldn't create render pass")
		
		self.render_pass = render_pass

	def create_frame_buffers(self):
		self.framebuffers = (vk.Framebuffer*self.image_data['count'])()

		for index, view in enumerate(self.sc_image_views):
			attachments = (vk.ImageView*2)(
				view, 
				self.depth.image_view
			)

			create_info = vk.FramebufferCreateInfo(
				s_type=vk.STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO,
				render_pass=self.render_pass,
				attachment_count=2,
				attachments=attachments,
				width=self.image_data['extent'].width,
				height=self.image_data['extent'].height,
				layers=1
			)

			fb = vk.Framebuffer(0)
			self.CreateFramebuffer(self.device, byref(create_info), None, byref(fb))
			self.framebuffers[index] = fb

	def destroy_swap_chain(self):
		for view in self.sc_image_views:
			self.DestroyImageView(self.device, view, None)

		self.DestroySwapchainKHR(self.device, self.swap_chain, None)

	def __init__(self, debug):
		# The Vulkan instance (VkInstance)
		self.instance = vk.Instance(0)
		# The Vulkan debugger, which prints errors and warnings 
		# to the console when enabled (VkDebugReportCallbackEXT)
		self.debugger = vk.DebugReportCallbackEXT(0)
		# The Pygame window, wrapped with a Vulkan surface (VkSurfaceKHR)
		self.window = None
		# The surface (VkSurfaceKHR) referenced in Window, for better readabilitiy
		self.surface = None
		# The selected graphics card (VkPhysicalDevice)
		self.gpu = None
		# The logical device that handles virtual memory inside Vulkan (VkDevice)
		self.device = None
		# The queue that is filled when draw calls are completed (VkQueue)
		self.graphics = {'index': None, 'queue': None }
		# The queue that is filled when images are ready to be presented (VkQueue)
		self.present = {'index': None, 'queue': None }
		# The Swap Chain: the virtual device that "swaps" 
		# through the data in the queues defined above (VkSwapchainKHR)
		self.swap_chain = None
		# Information that will be used to determine sizes and formats of images and buffers
		self.image_data = {'color_format': None, 'depth_format': None,
						   'count': None, 'extent': None }
		# A list of image views to interpret the above images (VkImageView[])
		self.sc_image_views = None

		self.pipeline_cache = None

		# The pool that will store buffers containing draw calls (VkCommandPool)
		self.pool = None
		# The Image that will hold color info (Image)
		self.color = None
		# The Image that will hold depth info (Image)
		self.depth = None
		# The defined path each set of draw calls will take (VkRenderPass)
		self.render_pass = None
		# The buffers the image views will be stored in to display on screen (VkFramebuffer[])
		self.framebuffers = None

		self.samplers = { }

		self.create_instance(debug)
		if debug:
			self.create_debugger()
		self.window = Window(self, {'width': 800, 'height': 450})
		self.surface = self.window.surface
		self.pick_gpu()
		self.create_device(debug)
		self.fill_queues()
		self.create_swap_chain()
		self.create_sc_views()
		self.create_pipeline_cache()
		self.create_pool()

		self.color = Image(
			self, 
			self.image_data['extent'],
			self.image_data['color_format'],
			1,
			vk.SAMPLE_COUNT_1_BIT,
			vk.IMAGE_USAGE_TRANSIENT_ATTACHMENT_BIT | vk.IMAGE_USAGE_COLOR_ATTACHMENT_BIT,
			vk.MEMORY_PROPERTY_DEVICE_LOCAL_BIT,
			vk.IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,
			vk.IMAGE_ASPECT_COLOR_BIT
		)

		self.depth = Image(
			self, 
			self.image_data['extent'],
			self.image_data['depth_format'],
			1,
			vk.SAMPLE_COUNT_1_BIT,
			vk.IMAGE_USAGE_DEPTH_STENCIL_ATTACHMENT_BIT,
			vk.MEMORY_PROPERTY_DEVICE_LOCAL_BIT,
			vk.IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL,
			vk.IMAGE_ASPECT_DEPTH_BIT
		)

		self.create_render_pass()
		self.create_frame_buffers()

	def cleanup(self):

		for s in self.samplers.values():
			self.DestroySampler(self.device, s, None)

		for fb in self.framebuffers:
			self.DestroyFramebuffer(self.device, fb, None)
		self.DestroyRenderPass(self.device, self.render_pass, None)

		self.color.cleanup()
		self.depth.cleanup()

		self.DestroyCommandPool(self.device, self.pool, None)
		self.DestroyPipelineCache(self.device, self.pipeline_cache, None)
		self.destroy_swap_chain()
		self.DestroyDevice(self.device, None)
		self.DestroyDebugReportCallbackEXT(self.instance, self.debugger, None)
		self.DestroyInstance(self.instance, None)

	def _find_supported_format(self, candidates, tiling, feats):
		for c in candidates:
			props = vk.FormatProperties(0)
			self.GetPhysicalDeviceFormatProperties(self.gpu, c, byref(props))

			if tiling == vk.IMAGE_TILING_LINEAR and (props.linear_tiling_features & feats) == feats:
				return c
			elif tiling == vk.IMAGE_TILING_OPTIMAL and (props.optimal_tiling_features & feats) == feats:
				return c

		raise RuntimeError("Unable to find a supported format")

	def find_depth_format(self):
		return self._find_supported_format(
			[vk.FORMAT_D32_SFLOAT, vk.FORMAT_D32_SFLOAT_S8_UINT, vk.FORMAT_D24_UNORM_S8_UINT],
			vk.IMAGE_TILING_OPTIMAL,
			vk.FORMAT_FEATURE_DEPTH_STENCIL_ATTACHMENT_BIT
		)

	def get_memory_type(self, bits, props):
		mem_props = vk.PhysicalDeviceMemoryProperties()
		self.GetPhysicalDeviceMemoryProperties(self.gpu, byref(mem_props))

		for index, mem_t in enumerate(mem_props.memory_types):
			if (bits & 1) == 1:
				if mem_t.property_flags & props == props:
					return index
			bits >>= 1

		return None

	def start_command(self):
		b_allocate_info = vk.CommandBufferAllocateInfo(
			s_type=vk.STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO,
			level=vk.COMMAND_BUFFER_LEVEL_PRIMARY,
			command_pool=self.pool,
			command_buffer_count=1
		)

		buff = vk.CommandBuffer(0)
		self.AllocateCommandBuffers(self.device, byref(b_allocate_info), byref(buff))

		begin_info = vk.CommandBufferBeginInfo(
			s_type=vk.STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO
		)

		self.BeginCommandBuffer(buff, byref(begin_info))
		return buff


	def end_command(self, buff):
		self.EndCommandBuffer(buff)

		submit_info = vk.SubmitInfo(
			s_type=vk.STRUCTURE_TYPE_SUBMIT_INFO,
			command_buffer_count=1,
			command_buffers=pointer(buff)
		)

		self.QueueSubmit(self.graphics['queue'], 1, byref(submit_info), 0)
		self.QueueWaitIdle(self.graphics['queue'])

		self.FreeCommandBuffers(self.device, self.pool, 1, byref(buff))

	def get_texture_sampler(self, mip):
		if mip in self.samplers.keys():
			return self.samplers[mip]
		else:
			self.samplers[mip] = make_texture_sampler(self, mip)
			return self.samplers[mip]

def debug_function(flags, object_type, object, location, message_code, layer, message, user_data):
	if flags & vk.DEBUG_REPORT_ERROR_BIT_EXT:
		_type = 'ERROR'
	elif flags & vk.DEBUG_REPORT_WARNING_BIT_EXT:
		_type = 'WARNING'

	print("DisKovery: VULKAN {}: {}\n".format(_type, message[::].decode()))
	return 0