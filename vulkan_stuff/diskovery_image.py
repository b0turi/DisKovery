from vulkan import *
from diskovery_vulkan import find_memory_type
import diskovery

def make_image_view(device, image, form, aspects, mip):
	subresource = VkImageSubresourceRange(
		aspectMask=aspects,
		baseMipLevel=0,
		levelCount=mip,
		baseArrayLayer=0,
		layerCount=1
	)

	image_view_create = VkImageViewCreateInfo(
		sType=VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO,
		image=image,
		viewType=VK_IMAGE_VIEW_TYPE_2D,
		format=form,
		subresourceRange=subresource
	)

	image_view = vkCreateImageView(device, image_view_create, None)
	return image_view

def change_layout(image, form, old, new, mip):
	cmd = diskovery.start_command()

	subresource = VkImageSubresourceRange()

	if new == VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL:
		subresource.aspectMask = VK_IMAGE_ASPECT_DEPTH_BIT

		if form == VK_FORMAT_D32_SFLOAT_S8_UINT or form == VK_FORMAT_D24_UNORM_S8_UINT:
			subresource.aspectMask |= VK_IMAGE_ASPECT_STENCIL_BIT
	else:
		subresource.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT

	subresource.baseMipLevel = 0
	subresource.levelCount = mip
	subresource.baseArrayLayer = 0
	subresource.layerCount = 1

	src_access_mask = None
	dst_access_mask = None

	src_stage = None
	dst_stage = None

	if old == VK_IMAGE_LAYOUT_UNDEFINED and new == VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL:
		src_access_mask = 0
		dst_access_mask = VK_ACCESS_TRANSFER_WRITE_BIT

		src_stage = VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT
		dst_stage = VK_PIPELINE_STAGE_TRANSFER_BIT
	elif old == VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL and new == VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL:
		src_access_mask = VK_ACCESS_TRANSFER_WRITE_BIT
		dst_access_mask = VK_ACCESS_SHADER_READ_BIT

		src_stage = VK_PIPELINE_STAGE_TRANSFER_BIT
		dst_stage = VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT
	elif old == VK_IMAGE_LAYOUT_UNDEFINED and new == VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL:
		src_access_mask = 0
		dst_access_mask = VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_READ_BIT | VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT

		src_stage = VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT
		dst_stage = VK_PIPELINE_STAGE_EARLY_FRAGMENT_TESTS_BIT
	elif old == VK_IMAGE_LAYOUT_UNDEFINED and new == VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL:
		src_access_mask = 0
		dst_access_mask = VK_ACCESS_COLOR_ATTACHMENT_READ_BIT | VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT

		src_stage = VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT
		dst_stage = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT
	else:
		print("unsupported layout transition!")

	barrier = VkImageMemoryBarrier(
		sType=VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER,
		oldLayout=old,
		newLayout=new,
		srcQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED,
		dstQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED,
		image=image,
		srcAccessMask=src_access_mask,
		dstAccessMask=dst_access_mask,
		subresourceRange=subresource
	)

	vkCmdPipelineBarrier(cmd, src_stage, dst_stage, 0, 0, None, 0, None, 1, barrier)
	
	diskovery.end_command(cmd)


class Image:
	def __init__(self, extent, form, mip, samples, usage, props, layout, aspects):

		self.image = None
		self.image_view = None

		self.memory = None

		self.make_image(extent.width, extent.height, mip, samples, form, usage, props)
		change_layout(self.image, form, VK_IMAGE_LAYOUT_UNDEFINED, layout, mip)
		self.image_view = make_image_view(diskovery.device(), self.image, form, aspects, mip)

	def make_image(self, width, height, mip, samples, form, usage, props):
		image_create = VkImageCreateInfo(
			sType=VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO,
			imageType=VK_IMAGE_TYPE_2D,
			extent=VkExtent3D(width, height, 1),
			mipLevels=mip,
			arrayLayers=1,
			format=form,
			tiling=VK_IMAGE_TILING_OPTIMAL,
			initialLayout=VK_IMAGE_LAYOUT_UNDEFINED,
			usage=usage,
			samples=samples,
			sharingMode=VK_SHARING_MODE_EXCLUSIVE
		)

		self.image = vkCreateImage(diskovery.device(), image_create, None)

		mem_req = vkGetImageMemoryRequirements(diskovery.device(), self.image)

		alloc_info = VkMemoryAllocateInfo(
			sType=VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
			allocationSize=mem_req.size,
			memoryTypeIndex=find_memory_type(
				diskovery.physical_device(),
				mem_req.memoryTypeBits,
				props)
		)

		self.memory = vkAllocateMemory(diskovery.device(), alloc_info, None)

		vkBindImageMemory(diskovery.device(), self.image, self.memory, 0)

	def cleanup(self):
		vkDestroyImageView(diskovery.device(), self.image_view, None)
		vkDestroyImage(diskovery.device(), self.image, None)
		vkFreeMemory(diskovery.device(), self.memory, None)
