import vk
from ctypes import *
import platform
from itertools import chain
from diskovery_window import Window

def debug_function(flags, object_type, object, location, message_code, layer, message, user_data):
	if flags & vk.DEBUG_REPORT_ERROR_BIT_EXT:
		_type = 'ERROR'
	elif flags & vk.DEBUG_REPORT_WARNING_BIT_EXT:
		_type = 'WARNING'

	print("DisKovery: VULKAN {}: {}\n".format(_type, message[::].decode()))
	return 0

class VulkanShit:
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
			next=None,
			user_data=None,
			flags=vk.DEBUG_REPORT_ERROR_BIT_EXT | vk.DEBUG_REPORT_WARNING_BIT_EXT,
			callback=callback_fn
		)
		debugger = vk.DebugReportCallbackEXT(0)
		result = self.CreateDebugReportCallbackEXT(
			self.instance, 
			byref(create_info), 
			None, 
			byref(debugger)
		)
		self.debugger = debugger

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

	def __init__(self):
		self.instance = vk.Instance(0)
		self.graphics = { 'index': None, 'queue': None}
		self.present = { 'index': None, 'queue': None}
		self.image_data = { }
		self.create_instance(True)
		self.window = Window(self, {'width': 800, 'height': 450})
		self.surface = self.window.surface
		self.create_debugger()
		self.pick_gpu()
		self.create_device(True)
		self.create_pool()

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

v = VulkanShit()