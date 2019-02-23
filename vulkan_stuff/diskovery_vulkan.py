from vulkan import *
from enum import Enum
import glm
from sys import getsizeof

# Miscellaneous Vulkan creation functions that didn't warrant their own class

# Used when a Vulkan command is not included in the Python wrapper
# to reflectively call the original C/C++ command
def get_vulkan_command(instance, cmd):
	return vkGetInstanceProcAddr(instance, cmd)

def make_render_pass(image_format, depth_format, device):
	color_attachment = VkAttachmentDescription(
		flags=0,
		format=image_format,
		samples=VK_SAMPLE_COUNT_1_BIT,
		loadOp=VK_ATTACHMENT_LOAD_OP_CLEAR,
		storeOp=VK_ATTACHMENT_STORE_OP_STORE,
		stencilLoadOp=VK_ATTACHMENT_LOAD_OP_DONT_CARE,
		stencilStoreOp=VK_ATTACHMENT_STORE_OP_DONT_CARE,
		initialLayout=VK_IMAGE_LAYOUT_UNDEFINED,
		finalLayout=VK_IMAGE_LAYOUT_PRESENT_SRC_KHR
	)

	depth_attachment = VkAttachmentDescription(
		flags=0,
		format=depth_format,
		samples=VK_SAMPLE_COUNT_1_BIT,
		loadOp=VK_ATTACHMENT_LOAD_OP_CLEAR,
		storeOp=VK_ATTACHMENT_STORE_OP_DONT_CARE,
		stencilLoadOp=VK_ATTACHMENT_LOAD_OP_DONT_CARE,
		stencilStoreOp=VK_ATTACHMENT_STORE_OP_DONT_CARE,
		initialLayout=VK_IMAGE_LAYOUT_UNDEFINED,
		finalLayout=VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL
	)

	# color_resolve = VkAttachmentDescription(
	# 	flags=0,
	# 	format=image_format,
	# 	samples=VK_SAMPLE_COUNT_1_BIT,
	# 	loadOp=VK_ATTACHMENT_LOAD_OP_DONT_CARE,
	# 	storeOp=VK_ATTACHMENT_STORE_OP_DONT_CARE,
	# 	stencilLoadOp=VK_ATTACHMENT_LOAD_OP_DONT_CARE,
	# 	stencilStoreOp=VK_ATTACHMENT_STORE_OP_DONT_CARE,
	# 	initialLayout=VK_IMAGE_LAYOUT_UNDEFINED,
	# 	finalLayout=VK_IMAGE_LAYOUT_PRESENT_SRC_KHR
	# )

	color_attachment_ref = VkAttachmentReference(
		attachment=0,
		layout=VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL
	)

	depth_attachment_ref = VkAttachmentReference(
		attachment=1,
		layout=VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL
	)

	# color_resolve_ref = VkAttachmentReference(
	# 	attachment=2,
	# 	layout=VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL
	# )

	sub_pass = VkSubpassDescription(
	    flags=0,
	    pipelineBindPoint=VK_PIPELINE_BIND_POINT_GRAPHICS,
	    inputAttachmentCount=0,
	    pInputAttachments=None,
	    #pResolveAttachments=[color_resolve_ref],
	    pDepthStencilAttachment=[depth_attachment_ref],
	    preserveAttachmentCount=0,
	    pPreserveAttachments=None,
	    colorAttachmentCount=1,
	    pColorAttachments=[color_attachment_ref])

	dependency = VkSubpassDependency(
		dependencyFlags=0,
		srcSubpass=VK_SUBPASS_EXTERNAL,
		dstSubpass=0,
		srcStageMask=VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
		srcAccessMask=0,
		dstStageMask=VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
		dstAccessMask=VK_ACCESS_COLOR_ATTACHMENT_READ_BIT | VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT)

	render_pass_create = VkRenderPassCreateInfo(
		flags=0,
		sType=VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO,
		attachmentCount=2,
		pAttachments=[color_attachment, depth_attachment],
		subpassCount=1,
		pSubpasses=[sub_pass],
		dependencyCount=1,
		pDependencies=[dependency])

	return vkCreateRenderPass(device, render_pass_create, None)

def destroy_render_pass(device, render_pass):
	vkDestroyRenderPass(device, render_pass, None)

def make_frame_buffers(color, depth, image_views, render_pass, extent, device):
	framebuffers = []
	for image in image_views:
		attachments = [image, depth]
		framebuffer_create = VkFramebufferCreateInfo(
			sType=VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO,
			flags=0,
			renderPass=render_pass,
			attachmentCount=len(attachments),
			pAttachments=attachments,
			width=extent.width,
			height=extent.height,
			layers=1)
		framebuffers.append(vkCreateFramebuffer(device, framebuffer_create, None))

	return framebuffers

def destroy_frame_buffers(device, framebuffers):
	for f in framebuffers:
	    vkDestroyFramebuffer(device, f, None)

def find_memory_type(physical_device, mem_filter, properties):
	mem_props = vkGetPhysicalDeviceMemoryProperties(physical_device)

	for i in range(0, mem_props.memoryTypeCount):
		if (mem_filter & (1 << i)) and (
			mem_props.memoryTypes[i].propertyFlags & properties) == properties:
			return i

	print("Unable to find suitable memory type!")

class BindingType(Enum):
	UNIFORM_BUFFER = 0
	TEXTURE_SAMPLER = 1

class UniformType(Enum):
	MVP_MATRIX = 0
	LIGHT = 1

class MVPMatrix():
	model = glm.mat4()
	view = glm.mat4()
	projection = glm.mat4()

class Light():
	position = glm.vec4()
	color = glm.vec4()

def get_uniform_size(uniform_type):
	if uniform_type == UniformType.MVP_MATRIX:
		return getsizeof(MVPMatrix)
	if uniform_type == UniformType.LIGHT:
		return getsizeof(Light)

def make_command_pool(device, index):
	command_pool_create = VkCommandPoolCreateInfo(
		sType=VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO,
		queueFamilyIndex=index,
		flags=0)
	return vkCreateCommandPool(device, command_pool_create, None)

def destroy_command_pool(device, pool):
	vkDestroyCommandPool(device, pool, None)

def find_supported_format(candidates, tiling, features, device):
	for form in candidates:
		props = vkGetPhysicalDeviceFormatProperties(device, form)

		if tiling == VK_IMAGE_TILING_LINEAR and (props.linearTilingFeatures & features) == features:
			return form
		elif tiling == VK_IMAGE_TILING_OPTIMAL and (props.optimalTilingFeatures & features) == features:
			return form

	print("Unable to find supported format!")

def find_depth_format(physical_device):
	return find_supported_format(
		[VK_FORMAT_D32_SFLOAT, VK_FORMAT_D32_SFLOAT_S8_UINT, VK_FORMAT_D24_UNORM_S8_UINT],
		VK_IMAGE_TILING_OPTIMAL,
		VK_FORMAT_FEATURE_DEPTH_STENCIL_ATTACHMENT_BIT,
		physical_device
	)