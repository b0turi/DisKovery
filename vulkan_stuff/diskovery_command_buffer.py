from vulkan import *
import diskovery 

def make_command_pool(device, index):
	command_pool_create = VkCommandPoolCreateInfo(
		sType=VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO,
		queueFamilyIndex=index,
		flags=0)
	return vkCreateCommandPool(device, command_pool_create, None)

def destroy_command_pool(device, pool):
	vkDestroyCommandPool(device, pool, None)

def start_command():
	allocate_info = VkCommandBufferAllocateInfo(
		sType=VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO,
		level=VK_COMMAND_BUFFER_LEVEL_PRIMARY,
		commandPool=diskovery.pool(),
		commandBufferCount=1
	)

	buff = vkAllocateCommandBuffers(diskovery.device(), allocate_info)

	begin_info = VkCommandBufferBeginInfo(
		sType=VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO,
		flags=VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT
	)

	vkBeginCommandBuffer(buff, begin_info)
	return buff

def end_command(buff):
	vkEndCommandBuffer(buff)

	submit_info = VkSubmitInfo(
		sType=VK_STRUCTURE_TYPE_SUBMIT_INFO,
		commandBufferCount=1,
		pCommandBuffers=buff
	)

	vkQueueSubmit(diskovery.graphics_queue(), 1, submit_info, VK_NULL_HANDLE)
	vkQueueWaitIdle(diskovery.graphics_queue())

	vkFreeCommandBuffers(diskovery.device(), diskovery.pool(), 1, buff)

class CommandBuffer:
	def __init__(self, pool, device, framebuffers, render_pass, extent, pipeline):
		self.pool = pool
		self.framebuffers = framebuffers
		self.render_pass = render_pass
		self.extent = extent
		self.pipeline = pipeline
		self.device = device


		self.buffers = None

		self.make_command_buffers()

	def make_command_buffers(self):

		command_buffers_create = VkCommandBufferAllocateInfo(
			sType=VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO,
			commandPool=self.pool,
			level=VK_COMMAND_BUFFER_LEVEL_PRIMARY,
			commandBufferCount=len(self.framebuffers)
		)

		self.buffers = vkAllocateCommandBuffers(self.device, command_buffers_create)

		for i, command_buffer in enumerate(self.buffers):

			command_buffer_begin_create = VkCommandBufferBeginInfo(
				sType=VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO,
				flags=VK_COMMAND_BUFFER_USAGE_SIMULTANEOUS_USE_BIT,
				pInheritanceInfo=None
			)

			vkBeginCommandBuffer(command_buffer, command_buffer_begin_create)

			# Create render pass
			render_area = VkRect2D(offset=VkOffset2D(x=0, y=0),
									extent=self.extent)
			color = VkClearColorValue(float32=[0, 1, 0, 1])
			clear_value = VkClearValue(color=color)

			render_pass_begin_create = VkRenderPassBeginInfo(
				sType=VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO,
				renderPass=self.render_pass,
				framebuffer=self.framebuffers[i],
				renderArea=render_area,
				clearValueCount=1,
				pClearValues=[clear_value])

			vkCmdBeginRenderPass(command_buffer, render_pass_begin_create, VK_SUBPASS_CONTENTS_INLINE)

			# Bing pipeline
			vkCmdBindPipeline(command_buffer, VK_PIPELINE_BIND_POINT_GRAPHICS, self.pipeline)

			# Draw
			vkCmdDraw(command_buffer, 3, 1, 0, 0)

			# End
			vkCmdEndRenderPass(command_buffer)
			vkEndCommandBuffer(command_buffer)

	def cleanup(self):
		vkFreeCommandBuffers(self.device, self.pool, len(self.buffers), self.buffers)