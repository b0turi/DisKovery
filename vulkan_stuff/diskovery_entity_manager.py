import diskovery
from vulkan import *
from diskovery_vulkan import get_vulkan_command

class EntityManager:
	def __init__(self):
		self._entities = {}

		self.buffers = None
		self.buffers = self.create_command_buffers()

		self.create_semaphores()

	def add_entity(self, name, entity):
		self._entities[name] = entity
		self.create_command_buffers()

	def remove_entity(self, name):
		self._entities.remove(name)
		self.create_command_buffers()

	def create_semaphores(self):
		semaphore_create = VkSemaphoreCreateInfo(
		    sType=VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO,
		    flags=0)

		self.image_available = vkCreateSemaphore(diskovery.device(), semaphore_create, None)
		self.render_finished = vkCreateSemaphore(diskovery.device(), semaphore_create, None)

		wait_semaphores = [self.image_available]
		wait_stages = [VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT]
		signal_semaphores = [self.render_finished]

		self.submit_create = VkSubmitInfo(
		    sType=VK_STRUCTURE_TYPE_SUBMIT_INFO,
		    waitSemaphoreCount=len(wait_semaphores),
		    pWaitSemaphores=wait_semaphores,
		    pWaitDstStageMask=wait_stages,
		    commandBufferCount=1,
		    pCommandBuffers=[self.buffers[0]],
		    signalSemaphoreCount=len(signal_semaphores),
		    pSignalSemaphores=signal_semaphores)

		self.present_create = VkPresentInfoKHR(
		    sType=VK_STRUCTURE_TYPE_PRESENT_INFO_KHR,
		    waitSemaphoreCount=1,
		    pWaitSemaphores=signal_semaphores,
		    swapchainCount=1,
		    pSwapchains=[diskovery.swap_chain()],
		    pImageIndices=[0],
		    pResults=None)


		# optimization to avoid creating a new array each time
		self.submit_list = ffi.new('VkSubmitInfo[1]', [self.submit_create])

	def create_command_buffers(self):

		if self.buffers != None:
			self.destroy_command_buffers()

		command_buffers_create = VkCommandBufferAllocateInfo(
			sType=VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO,
			commandPool=diskovery.pool(),
			level=VK_COMMAND_BUFFER_LEVEL_PRIMARY,
			commandBufferCount=diskovery.num_back_buffers()
		)

		buffs = vkAllocateCommandBuffers(diskovery.device(), command_buffers_create)

		for i, command_buffer in enumerate(buffs):

			command_buffer_begin_create = VkCommandBufferBeginInfo(
				sType=VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO,
				flags=VK_COMMAND_BUFFER_USAGE_SIMULTANEOUS_USE_BIT,
				pInheritanceInfo=None
			)

			vkBeginCommandBuffer(command_buffer, command_buffer_begin_create)

			render_area = VkRect2D(offset=VkOffset2D(x=0, y=0),
									extent=diskovery.extent())
			clear_color = VkClearColorValue(float32=[0, 1, 0, 1])
			clear_depth = VkClearDepthStencilValue(depth=1., stencil=0)

			clear_values = [VkClearValue(color=clear_color), VkClearValue(depthStencil=clear_depth)]

			render_pass_begin_create = VkRenderPassBeginInfo(
				sType=VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO,
				renderPass=diskovery.render_pass(),
				framebuffer=diskovery.framebuffer(i),
				renderArea=render_area,
				clearValueCount=2,
				pClearValues=clear_values)

			vkCmdBeginRenderPass(command_buffer, render_pass_begin_create, VK_SUBPASS_CONTENTS_INLINE)

			for entity in self._entities.values():

				vkCmdBindPipeline(command_buffer, VK_PIPELINE_BIND_POINT_GRAPHICS, diskovery.pipeline(entity.pipeline).pipeline_ref)

				buffers = [diskovery.mesh(entity.mesh).vertices.buffer]
				offsets = [0]
				vkCmdBindVertexBuffers(command_buffer, 0, 1, buffers, offsets)

				vkCmdBindIndexBuffer(command_buffer, diskovery.mesh(entity.mesh).indices.buffer, 0, VK_INDEX_TYPE_UINT32)

				vkCmdBindDescriptorSets(
					command_buffer, 
					VK_PIPELINE_BIND_POINT_GRAPHICS,
					diskovery.pipeline(entity.pipeline).pipeline_layout,
					0, 
					1,
					[entity.descriptor.sets[i]],
					0,
					None
				)

				vkCmdDrawIndexed(command_buffer, diskovery.mesh(entity.mesh).count, 1, 0, 0, 0)

			vkCmdEndRenderPass(command_buffer)
			vkEndCommandBuffer(command_buffer)

		return buffs

	def draw(self):

		

		image_index = get_vulkan_command(diskovery.instance(), "vkAcquireNextImageKHR")(
			diskovery.device(),
			diskovery.swap_chain(),
			UINT64_MAX,
			self.image_available,
			None
		)

		for name, entity in self._entities.items():
			entity.update(image_index)

		self.submit_create.pCommandBuffers[0] = self.buffers[image_index]
		vkQueueSubmit(diskovery.graphics_queue(), 1, self.submit_list, None)

		self.present_create.pImageIndices[0] = image_index
		get_vulkan_command(diskovery.instance(), "vkQueuePresentKHR")(diskovery.present_queue(), self.present_create)

	def destroy_command_buffers(self):
		vkFreeCommandBuffers(diskovery.device(), diskovery.pool(), len(self.buffers), self.buffers)


	def cleanup(self):
		vkDestroySemaphore(diskovery.device(), self.image_available, None)
		vkDestroySemaphore(diskovery.device(), self.render_finished, None)
		self.destroy_command_buffers()