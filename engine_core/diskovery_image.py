#!/bin/env/python

import vk
import math
import pygame
from ctypes import *
from diskovery_buffer import Buffer

class Image(object):
	def create_image(self, extent, mip, samp, form, use, props):

		create_info = vk.ImageCreateInfo(
			s_type=vk.STRUCTURE_TYPE_IMAGE_CREATE_INFO,
			image_type=vk.IMAGE_TYPE_2D,
			extent=vk.Extent3D(extent.width, extent.height, 1),
			mip_levels=mip,
			array_layers=1,
			samples=samp,
			tiling=vk.IMAGE_TILING_OPTIMAL,
			usage=use,
			format=form,
			sharing_mode=vk.SHARING_MODE_EXCLUSIVE
		)

		self.dk.CreateImage(self.dk.device, create_info, None, byref(self.image))

		mem_req = vk.MemoryRequirements()
		self.dk.GetImageMemoryRequirements(self.dk.device, self.image, byref(mem_req))

		mem_alloc_info = vk.MemoryAllocateInfo(
			s_type=vk.STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
			next=None,
			allocation_size=mem_req.size,
			memory_type_index=self.dk.get_memory_type(
				mem_req.memory_type_bits,
				props
			)
		)

		self.dk.AllocateMemory(self.dk.device, byref(mem_alloc_info), None, byref(self.memory))
		self.dk.BindImageMemory(self.dk.device, self.image, self.memory, 0)

	def set_layout(self, image, form, old, new, mip):
		cmd = self.dk.start_command()

		if new == vk.IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL:
			aspect_mask = vk.IMAGE_ASPECT_DEPTH_BIT

			if form == vk.FORMAT_D32_SFLOAT_S8_UINT or form == vk.FORMAT_D24_UNORM_S8_UINT:
				aspect_mask |= vk.IMAGE_ASPECT_STENCIL_BIT
		else:
			aspect_mask = vk.IMAGE_ASPECT_COLOR_BIT

		sub = vk.ImageSubresourceRange(
			aspect_mask=aspect_mask,
			base_mip_level=0,
			level_count=mip,
			base_array_layer=0,
			layer_count=1
		)

		src_access_mask = None
		dst_access_mask = None

		src_stage = None
		dst_stage = None

		if old == vk.IMAGE_LAYOUT_UNDEFINED and new == vk.IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL:
			src_access_mask = 0
			dst_access_mask = vk.ACCESS_TRANSFER_WRITE_BIT

			src_stage = vk.PIPELINE_STAGE_TOP_OF_PIPE_BIT
			dst_stage = vk.PIPELINE_STAGE_TRANSFER_BIT
		elif old == vk.IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL and new == vk.IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL:
			src_access_mask = vk.ACCESS_TRANSFER_WRITE_BIT
			dst_access_mask = vk.ACCESS_SHADER_READ_BIT

			src_stage = vk.PIPELINE_STAGE_TRANSFER_BIT
			dst_stage = vk.PIPELINE_STAGE_FRAGMENT_SHADER_BIT
		elif old == vk.IMAGE_LAYOUT_UNDEFINED and new == vk.IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL:
			src_access_mask = 0
			dst_access_mask = vk.ACCESS_DEPTH_STENCIL_ATTACHMENT_READ_BIT | vk.ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT

			src_stage = vk.PIPELINE_STAGE_TOP_OF_PIPE_BIT
			dst_stage = vk.PIPELINE_STAGE_EARLY_FRAGMENT_TESTS_BIT
		elif old == vk.IMAGE_LAYOUT_UNDEFINED and new == vk.IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL:
			src_access_mask = 0
			dst_access_mask = vk.ACCESS_COLOR_ATTACHMENT_READ_BIT | vk.ACCESS_COLOR_ATTACHMENT_WRITE_BIT

			src_stage = vk.PIPELINE_STAGE_TOP_OF_PIPE_BIT
			dst_stage = vk.PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT
		else:
			print("unsupported layout transition!")

		barrier = vk.ImageMemoryBarrier(
			s_type=vk.STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER,
			old_layout=old,
			new_layout=new,
			src_queue_family_index=vk.QUEUE_FAMILY_IGNORED,
			dst_queue_family_index=vk.QUEUE_FAMILY_IGNORED,
			image=image,
			src_access_mask=src_access_mask,
			dst_access_mask=dst_access_mask,
			subresource_range=sub
		)

		self.dk.CmdPipelineBarrier(
			cmd,
			src_stage,
			dst_stage,
			0, 0,
			None, 0,
			None, 1,
			byref(barrier)
		)

		self.dk.end_command(cmd)

		self.access_mask = dst_access_mask
		self.stage = dst_stage

	def swap_to_source(self, cmd):

		sub = vk.ImageSubresourceRange(
			aspect_mask=vk.IMAGE_ASPECT_COLOR_BIT,
			base_mip_level=0,
			level_count=1,
			base_array_layer=0,
			layer_count=1
		)

		barrier = vk.ImageMemoryBarrier(
			s_type=vk.STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER,
			old_layout=self.layout,
			new_layout=vk.IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
			src_queue_family_index=vk.QUEUE_FAMILY_IGNORED,
			dst_queue_family_index=vk.QUEUE_FAMILY_IGNORED,
			image=self.image,
			src_access_mask=self.access_mask,
			dst_access_mask=vk.ACCESS_TRANSFER_WRITE_BIT,
			subresource_range=sub
		)

		self.dk.CmdPipelineBarrier(
			cmd,
			self.stage,
			vk.PIPELINE_STAGE_TRANSFER_BIT,
			0, 0,
			None, 0,
			None, 1,
			byref(barrier)
		)

	def swap_from_source(self, cmd):
		sub = vk.ImageSubresourceRange(
			aspect_mask=vk.IMAGE_ASPECT_COLOR_BIT,
			base_mip_level=0,
			level_count=1,
			base_array_layer=0,
			layer_count=1
		)

		barrier = vk.ImageMemoryBarrier(
			s_type=vk.STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER,
			old_layout=vk.IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
			new_layout=self.layout,
			src_queue_family_index=vk.QUEUE_FAMILY_IGNORED,
			dst_queue_family_index=vk.QUEUE_FAMILY_IGNORED,
			image=self.image,
			src_access_mask=vk.ACCESS_TRANSFER_WRITE_BIT,
			dst_access_mask=self.access_mask,
			subresource_range=sub
		)

		self.dk.CmdPipelineBarrier(
			cmd,
			vk.PIPELINE_STAGE_TRANSFER_BIT,
			self.stage,
			0, 0,
			None, 0,
			None, 1,
			byref(barrier)
		)

	def create_image_view(self, form, aspects, mip):
		sub = vk.ImageSubresourceRange(
			aspect_mask=aspects,
			base_mip_level=0,
			level_count=mip,
			base_array_layer=0,
			layer_count=1
		)

		create_info = vk.ImageViewCreateInfo(
			s_type=vk.STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO,
			image=self.image,
			view_type=vk.IMAGE_VIEW_TYPE_2D,
			format=form,
			subresource_range=sub
		)

		self.dk.CreateImageView(
			self.dk.device,
			byref(create_info),
			None,
			byref(self.image_view)
		)


	def __init__(self, dk, extent, form, mip, samp, use, props, layout, aspects):
		self.dk = dk
		# The Vulkan image (VkImage) that will store the image data
		self.image = vk.Image(0)
		# The Vulkan image view (VkImageView) that will allow acces to the image
		self.image_view = vk.ImageView(0)
		# The allocated memory (VkDeviceMemory) that will store the image
		self.memory = vk.DeviceMemory(0)

		self.create_image(extent, mip, samp, form, use, props)
		# Newly created images have an undefined layout. This method
		# fills the image with its given layout.
		self.set_layout(self.image, form, vk.IMAGE_LAYOUT_UNDEFINED, layout, mip)
		self.layout = layout
		self.create_image_view(form, aspects, mip)

	def cleanup(self):
		self.dk.DestroyImageView(self.dk.device, self.image_view, None)
		self.dk.DestroyImage(self.dk.device, self.image, None)
		self.dk.FreeMemory(self.dk.device, self.memory, None)

def make_texture_sampler(dk, mip):
	sampler = vk.Sampler(0)

	create_info = vk.SamplerCreateInfo(
		s_type=vk.STRUCTURE_TYPE_SAMPLER_CREATE_INFO,
		mag_filter=vk.FILTER_LINEAR,
		min_filter=vk.FILTER_LINEAR,
		address_mode_U=vk.SAMPLER_ADDRESS_MODE_REPEAT,
		address_mode_V=vk.SAMPLER_ADDRESS_MODE_REPEAT,
		address_mode_W=vk.SAMPLER_ADDRESS_MODE_REPEAT,
		anisotropy_enable=vk.TRUE,
		max_anisotropy=16,
		border_color=vk.BORDER_COLOR_INT_OPAQUE_BLACK,
		unnormalized_coordinates=vk.FALSE,
		compare_enable=vk.FALSE,
		compare_op=vk.COMPARE_OP_ALWAYS,
		mipmap_mode=vk.SAMPLER_MIPMAP_MODE_LINEAR,
		min_lod=0,
		max_lod=mip,
		mip_lod_bias=0
	)

	dk.CreateSampler(dk.device, byref(create_info), None, byref(sampler))
	return sampler

def buffer_to_image(dk, buff, image, width, height):
	cmd = dk.start_command()

	sub = vk.ImageSubresourceLayers(
		aspect_mask=vk.IMAGE_ASPECT_COLOR_BIT,
		mip_level=0,
		base_array_layer=0,
		layer_count=1,
	)

	region = vk.BufferImageCopy(
		image_subresource=sub,
		image_offset=vk.Offset3D(0, 0, 0),
		image_extent=vk.Extent3D(width, height, 1)
	)

	dk.CmdCopyBufferToImage(
		cmd,
		buff,
		image,
		vk.IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
		1,
		byref(region)
	)

	dk.end_command(cmd)

def image_to_buffer(dk, image, buff, region):
	cmd = dk.start_command()
	image.swap_to_source(cmd)

	dk.CmdCopyImageToBuffer(
		cmd,
		image.image,
		vk.IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
		buff,
		1,
		byref(region)
	)

	image.swap_from_source(cmd)
	dk.end_command(cmd)

class Texture(Image):

	def _generate_mipmaps(self, wid, hei, mip):
		props = vk.FormatProperties()
		self.dk.GetPhysicalDeviceFormatProperties(self.dk.gpu, vk.FORMAT_R8G8B8A8_UNORM, byref(props))

		cmd = self.dk.start_command()

		sub = vk.ImageSubresourceRange(
			aspect_mask=vk.IMAGE_ASPECT_COLOR_BIT,
			base_array_layer=0,
			layer_count=1,
			level_count=1
		)

		barrier = vk.ImageMemoryBarrier(
			s_type=vk.STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER,
			image=self.image,
			src_queue_family_index=vk.QUEUE_FAMILY_IGNORED,
			dst_queue_family_index=vk.QUEUE_FAMILY_IGNORED,
			subresource_range=sub
		)

		w = wid
		h = hei

		for i in range(1, mip):
			barrier.old_layout = vk.IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL
			barrier.new_layout = vk.IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL
			barrier.src_access_mask = vk.ACCESS_TRANSFER_WRITE_BIT
			barrier.dst_access_mask = vk.ACCESS_TRANSFER_READ_BIT
			barrier.subresource_range.base_mip_level = i - 1

			self.dk.CmdPipelineBarrier(
				cmd,
				vk.PIPELINE_STAGE_TRANSFER_BIT,
				vk.PIPELINE_STAGE_TRANSFER_BIT,
				0, 0, None,
				0, None,
				1, byref(barrier)
			)

			src_offsets = (vk.Offset3D * 2)(
				vk.Offset3D(0,0,0),
				vk.Offset3D(int(w), int(h), 1)
			)

			dst_offsets = (vk.Offset3D * 2)(
				vk.Offset3D(0,0,0),
				vk.Offset3D(
					int(w/2) if w > 1 else 1,
					int(h/2) if h > 1 else 1,
					1
				)
			)

			src_sub = vk.ImageSubresourceLayers(
				aspect_mask=vk.IMAGE_ASPECT_COLOR_BIT,
				mip_level=i-1,
				base_array_layer=0,
				layer_count=1
			)
			dst_sub = vk.ImageSubresourceLayers(
				aspect_mask=vk.IMAGE_ASPECT_COLOR_BIT,
				mip_level=i,
				base_array_layer=0,
				layer_count=1
			)
			blit = vk.ImageBlit(
				src_offsets=src_offsets,
				src_subresource=src_sub,
				dst_offsets=dst_offsets,
				dst_subresource=dst_sub
			)

			self.dk.CmdBlitImage(
				cmd,
				self.image,
				vk.IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
				self.image,
				vk.IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
				1, byref(blit),
				vk.FILTER_LINEAR
			)

			barrier.old_layout = vk.IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL
			barrier.new_layout = vk.IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL
			barrier.src_access_mask = vk.ACCESS_TRANSFER_READ_BIT
			barrier.dst_access_mask = vk.ACCESS_SHADER_READ_BIT

			self.dk.CmdPipelineBarrier(cmd,
				vk.PIPELINE_STAGE_TRANSFER_BIT,
				vk.PIPELINE_STAGE_FRAGMENT_SHADER_BIT,
				0, 0,
				None, 0,
				None, 1,
				byref(barrier)
			)

			if w > 1:
				w = int(w/2)
			if h > 1:
				h = int(h/2)

		barrier.subresource_range.base_mip_level = mip - 1
		barrier.old_layout = vk.IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL
		barrier.new_layout = vk.IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL
		barrier.src_access_mask = vk.ACCESS_TRANSFER_WRITE_BIT
		barrier.dst_access_mask = vk.ACCESS_SHADER_READ_BIT

		self.dk.CmdPipelineBarrier(
			cmd,
			vk.PIPELINE_STAGE_TRANSFER_BIT,
			vk.PIPELINE_STAGE_FRAGMENT_SHADER_BIT,
			0, 0,
			None,
			0, None,
			1, byref(barrier)
		)

		self.dk.end_command(cmd)

	def __init__(self, dk, filename):
		self.dk = dk
		img = pygame.image.load(filename).convert_alpha()

		extent = vk.Extent2D(width=img.get_width(), height=img.get_height())
		size = extent.width * extent.height * 4

		arr = pygame.PixelArray(img)

		self.mip = int(math.floor(math.log2(max(extent.width, extent.height))) + 1)

		data = (c_ubyte*size)()

		for i in range(0, extent.height):
			for j in range(0, extent.width):
				channels = img.unmap_rgb(arr[j, i])
				ind = i * extent.width * 4 + j * 4
				data[ind] = channels[0]
				data[ind + 1] = channels[1]
				data[ind + 2] = channels[2]
				data[ind + 3] = channels[3]

		Image.__init__(
			self,
			dk,
			extent,
			vk.FORMAT_R8G8B8A8_UNORM,
			self.mip,
			vk.SAMPLE_COUNT_1_BIT,
			vk.IMAGE_USAGE_TRANSFER_SRC_BIT |
			vk.IMAGE_USAGE_TRANSFER_DST_BIT |
			vk.IMAGE_USAGE_SAMPLED_BIT,
			vk.MEMORY_PROPERTY_DEVICE_LOCAL_BIT,
			vk.IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
			vk.IMAGE_ASPECT_COLOR_BIT
		)

		staging_buffer = Buffer(dk, size, data)
		buffer_to_image(
			dk,
			staging_buffer.buffer,
			self.image,
			extent.width,
			extent.height
		)
		staging_buffer.cleanup()

		self.filename = filename
		self._generate_mipmaps(extent.width, extent.height, self.mip)
