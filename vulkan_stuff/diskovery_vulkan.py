from vulkan import *

# Miscellaneous Vulkan creation functions that didn't warrant their own class

# Used when a Vulkan command is not included in the Python wrapper
# to reflectively call the original C/C++ command
def get_vulkan_command(instance, cmd):
	return vkGetInstanceProcAddr(instance, cmd)

def make_render_pass(surface_format, device):
	color_attachment = VkAttachmentDescription(
		flags=0,
		format=surface_format.format,
		samples=VK_SAMPLE_COUNT_1_BIT,
		loadOp=VK_ATTACHMENT_LOAD_OP_CLEAR,
		storeOp=VK_ATTACHMENT_STORE_OP_STORE,
		stencilLoadOp=VK_ATTACHMENT_LOAD_OP_DONT_CARE,
		stencilStoreOp=VK_ATTACHMENT_STORE_OP_DONT_CARE,
		initialLayout=VK_IMAGE_LAYOUT_UNDEFINED,
		finalLayout=VK_IMAGE_LAYOUT_PRESENT_SRC_KHR
		)

	color_attachment_ref = VkAttachmentReference(
		attachment=0,
		layout=VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL)

	sub_pass = VkSubpassDescription(
	    flags=0,
	    pipelineBindPoint=VK_PIPELINE_BIND_POINT_GRAPHICS,
	    inputAttachmentCount=0,
	    pInputAttachments=None,
	    pResolveAttachments=None,
	    pDepthStencilAttachment=None,
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
		attachmentCount=1,
		pAttachments=[color_attachment],
		subpassCount=1,
		pSubpasses=[sub_pass],
		dependencyCount=1,
		pDependencies=[dependency])

	return vkCreateRenderPass(device, render_pass_create, None)

def destroy_render_pass(device, render_pass):
	vkDestroyRenderPass(device, render_pass, None)

def make_frame_buffers(image_views, render_pass, extent, device):
	framebuffers = []
	for image in image_views:
		attachments = [image]
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