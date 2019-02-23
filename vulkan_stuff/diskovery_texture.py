from diskovery_image import Image
from diskovery_buffer import Buffer
from vulkan import *
import diskovery
import pygame
import ctypes

def make_texture_sampler(mip):
	sampler_create = VkSamplerCreateInfo(
		sType=VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO,
		magFilter=VK_FILTER_LINEAR,
		minFilter=VK_FILTER_LINEAR,
		addressModeU=VK_SAMPLER_ADDRESS_MODE_REPEAT,
		addressModeV=VK_SAMPLER_ADDRESS_MODE_REPEAT,
		addressModeW=VK_SAMPLER_ADDRESS_MODE_REPEAT,
		anisotropyEnable=VK_TRUE,
		maxAnisotropy=16,
		borderColor=VK_BORDER_COLOR_INT_OPAQUE_BLACK,
		unnormalizedCoordinates=VK_FALSE,
		compareEnable=VK_FALSE,
		compareOp=VK_COMPARE_OP_ALWAYS,
		mipmapMode=VK_SAMPLER_MIPMAP_MODE_LINEAR,
		minLod=0,
		maxLod=float(mip),
		mipLodBias=0
	)

	sampler = vkCreateSampler(diskovery.device(), sampler_create, None)

	return sampler

def buffer_to_image(buff, image, width, height):
	cmd = diskovery.start_command()

	subresource = VkImageSubresourceLayers()
	subresource.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT
	subresource.mipLevel = 0
	subresource.baseArrayLayer = 0
	subresource.layerCount = 1

	region = VkBufferImageCopy()
	region.bufferOffset = 0
	region.bufferRowLength = 0
	region.bufferImageHeight = 0
	region.imageSubresource = subresource
	region.imageOffset = [0, 0, 0]
	region.imageExtent = [width, height, 1]

	vkCmdCopyBufferToImage(cmd, buff, image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, region)
	diskovery.end_command(cmd)

class Texture(Image):
	def __init__(self, filename):
		surface = pygame.image.load(filename)
		
		extent = VkExtent2D(width=surface.get_width(), height=surface.get_height())
		size = extent.width * extent.height * 4
		pixel_data = bytearray(surface.get_buffer().raw)

		Image.__init__(
			self,
			extent, 
			VK_FORMAT_R8G8B8A8_UNORM,
			1,
			VK_SAMPLE_COUNT_1_BIT,
			VK_IMAGE_USAGE_TRANSFER_SRC_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT | VK_IMAGE_USAGE_SAMPLED_BIT,
			VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT,
			VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
			VK_IMAGE_ASPECT_COLOR_BIT
		)

		staging_buffer = Buffer(size, pixel_data)
		buffer_to_image(staging_buffer.buffer, self.image, extent.width, extent.height)
		staging_buffer.cleanup()

		# generate_mipmaps()