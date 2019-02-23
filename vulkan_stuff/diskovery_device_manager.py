#!/bin/env python

from vulkan import *
from diskovery_vulkan import get_vulkan_command

layers = ['VK_LAYER_LUNARG_standard_validation']

def debug_callback(*args):
	print('DisKovery - Vulkan Error: ' + args[5] + ' ' + args[6] + '\n\n')
	return 0

class DeviceManager:
	def __init__(self, window):
		self.instance = window.instance
		self.surface = window.surface

		self.debugger = None
		self.physical_device = None
		self.logical_device = None

		self.graphics_queue = { "index": None, "queue": None }
		self.present_queue = { "index": None, "queue": None }

		self.make_debugger()
		self.choose_physical_device()
		self.make_logical_device()

	def make_debugger(self):
		debug_create = VkDebugReportCallbackCreateInfoEXT(
			sType=VK_STRUCTURE_TYPE_DEBUG_REPORT_CALLBACK_CREATE_INFO_EXT,
			flags=VK_DEBUG_REPORT_ERROR_BIT_EXT | VK_DEBUG_REPORT_WARNING_BIT_EXT,
			pfnCallback=debug_callback
		)

		self.debugger = get_vulkan_command(
			self.instance, "vkCreateDebugReportCallbackEXT")(
			self.instance, debug_create, None)

	def choose_physical_device(self):
		physical_devices = vkEnumeratePhysicalDevices(self.instance)

		# TODO: more involved process of graphics card selection

		self.physical_device = physical_devices[0]

	def make_logical_device(self):

		queue_families = vkGetPhysicalDeviceQueueFamilyProperties(
			physicalDevice=self.physical_device)

		for i, queue_family in enumerate(queue_families):
			support_present = get_vulkan_command(
				self.instance, "vkGetPhysicalDeviceSurfaceSupportKHR")(
					physicalDevice=self.physical_device,
					queueFamilyIndex=i,
					surface=self.surface
				)

			if (queue_family.queueCount > 0 and 
				queue_family.queueFlags & VK_QUEUE_GRAPHICS_BIT):
				self.graphics_queue["index"] = i
				self.present_queue["index"] = i

		extensions = [VK_KHR_SWAPCHAIN_EXTENSION_NAME]

		queues_create = [VkDeviceQueueCreateInfo(
			sType=VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO,
			queueFamilyIndex=i,
			queueCount=1,
			pQueuePriorities=[1],
			flags=0
		)
		for i in {self.graphics_queue["index"], 
				  self.present_queue["index"]}]

		device_create = VkDeviceCreateInfo(
			sType=VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO,
			pQueueCreateInfos=queues_create,
			queueCreateInfoCount=len(queues_create),
			pEnabledFeatures=vkGetPhysicalDeviceFeatures(self.physical_device),
			flags=0,
			enabledLayerCount=len(layers),
			ppEnabledLayerNames=layers,
			enabledExtensionCount=len(extensions),
			ppEnabledExtensionNames=extensions
		)

		self.logical_device = vkCreateDevice(self.physical_device, device_create, None)

		self.graphics_queue["queue"] = vkGetDeviceQueue(
			device=self.logical_device,
			queueFamilyIndex=self.graphics_queue["index"], 
			queueIndex=0
		)

		self.present_queue["queue"] = vkGetDeviceQueue(
			device=self.logical_device,
			queueFamilyIndex=self.present_queue["index"], 
			queueIndex=0
		)

	def cleanup(self):
		vkDestroyDevice(self.logical_device, None)
		get_vulkan_command(self.instance, "vkDestroyDebugReportCallbackEXT")(
			self.instance, self.debugger, None)
