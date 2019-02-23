#!/bin/env python

from vulkan import *
from diskovery_vulkan import get_vulkan_command, find_depth_format

def get_surface_format(formats):
	for f in formats:
		if f.format == VK_FORMAT_UNDEFINED:
			return  f
		if (f.format == VK_FORMAT_B8G8R8A8_UNORM and
			f.colorSpace == VK_COLOR_SPACE_SRGB_NONLINEAR_KHR):
			return f
	return formats[0]

def get_surface_present_mode(present_modes):
	for p in present_modes:
		if p == VK_PRESENT_MODE_MAILBOX_KHR:
			return p
	return VK_PRESENT_MODE_FIFO_KHR;

def get_swap_extent(capabilities):
	uint32_max = 4294967295
	if capabilities.currentExtent.width != uint32_max:
		return VkExtent2D(width=capabilities.currentExtent.width,
						 height=capabilities.currentExtent.height)

	width = max(
		capabilities.minImageExtent.width,
		min(capabilities.maxImageExtent.width, WIDTH))
	height = max(
		capabilities.minImageExtent.height,
		min(capabilities.maxImageExtent.height, HEIGHT))
	actualExtent = VkExtent2D(width=width, height=height);
	return actualExtent


class SwapChain:
	def __init__(self, window, device_manager):
		self.window = window
		self.device_manager = device_manager

		self.swap_chain_ref = None

		self.surface_format = None
		self.present_mode = None
		self.extent = None
		self.image_count = 0

		self.images = None
		self.image_views = []

		self.transform = None

		self.make_swap_chain()

		self.image_format = self.surface_format.format
		self.depth_format = find_depth_format(device_manager.physical_device)

	def make_swap_chain(self):

		surface_capabilities = get_vulkan_command(self.window.instance, "vkGetPhysicalDeviceSurfaceCapabilitiesKHR")(
			physicalDevice=self.device_manager.physical_device, surface=self.window.surface)
		surface_formats = get_vulkan_command(self.window.instance, "vkGetPhysicalDeviceSurfaceFormatsKHR")(
			physicalDevice=self.device_manager.physical_device, surface=self.window.surface)
		surface_present_modes = get_vulkan_command(self.window.instance, "vkGetPhysicalDeviceSurfacePresentModesKHR")(
			physicalDevice=self.device_manager.physical_device, surface=self.window.surface)

		self.transform = surface_capabilities.currentTransform

		if not surface_formats or not surface_present_modes:
		    raise Exception('No available swapchain')

		self.surface_format = get_surface_format(surface_formats)
		self.present_mode = get_surface_present_mode(surface_present_modes)
		self.extent = get_swap_extent(surface_capabilities)
		self.image_count = surface_capabilities.minImageCount + 1;
		if surface_capabilities.maxImageCount > 0 and self.image_count > surface_capabilities.maxImageCount:
		    self.image_count = surface_capabilities.maxImageCount

		imageSharingMode = VK_SHARING_MODE_EXCLUSIVE
		queueFamilyIndexCount = 0
		pQueueFamilyIndices = None

		if self.device_manager.graphics_queue["index"] != self.device_manager.present_queue["index"]:
		    imageSharingMode = VK_SHARING_MODE_CONCURRENT
		    queueFamilyIndexCount = 2
		    pQueueFamilyIndices = [self.device_manager.graphics_queue["index"], 
		    						self.device_manager.present_queue["index"]]

		swapchain_create = VkSwapchainCreateInfoKHR(
		    sType=VK_STRUCTURE_TYPE_SWAPCHAIN_CREATE_INFO_KHR,
		    flags=0,
		    surface=self.window.surface,
		    minImageCount=self.image_count,
		    imageFormat=self.surface_format.format,
		    imageColorSpace=self.surface_format.colorSpace,
		    imageExtent=self.extent,
		    imageArrayLayers=1,
		    imageUsage=VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT,
		    imageSharingMode=imageSharingMode,
		    queueFamilyIndexCount=queueFamilyIndexCount,
		    pQueueFamilyIndices=pQueueFamilyIndices,
		    compositeAlpha=VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR,
		    presentMode=self.present_mode,
		    clipped=VK_TRUE,
		    oldSwapchain=None,
		    preTransform=self.transform)

		self.swap_chain_ref = get_vulkan_command(self.window.instance, "vkCreateSwapchainKHR")(
			self.device_manager.logical_device, swapchain_create, None)

		self.images = get_vulkan_command(self.window.instance, "vkGetSwapchainImagesKHR")(
			self.device_manager.logical_device, self.swap_chain_ref)

		for image in self.images:
		    subresourceRange = VkImageSubresourceRange(
		        aspectMask=VK_IMAGE_ASPECT_COLOR_BIT,
		        baseMipLevel=0,
		        levelCount=1,
		        baseArrayLayer=0,
		        layerCount=1)

		    components = VkComponentMapping(
		        r=VK_COMPONENT_SWIZZLE_IDENTITY,
		        g=VK_COMPONENT_SWIZZLE_IDENTITY,
		        b=VK_COMPONENT_SWIZZLE_IDENTITY,
		        a=VK_COMPONENT_SWIZZLE_IDENTITY)

		    imageview_create = VkImageViewCreateInfo(
		        sType=VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO,
		        image=image,
		        flags=0,
		        viewType=VK_IMAGE_VIEW_TYPE_2D,
		        format=self.surface_format.format,
		        components=components,
		        subresourceRange=subresourceRange)

		    self.image_views.append(vkCreateImageView(self.device_manager.logical_device, imageview_create, None))

	def cleanup(self):
		for i in self.image_views:
		    vkDestroyImageView(self.device_manager.logical_device, i, None)
		get_vulkan_command(self.window.instance, "vkDestroySwapchainKHR")(
			self.device_manager.logical_device, self.swap_chain_ref, None)