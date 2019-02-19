from vulkan import *

class SyncObjects:
	def __init__(self, device, buffers, swap_chain):
		self.mfif = 2
		self.device = device
		self.buffers = buffers
		self.swap_chain = swap_chain

		self.image_available = []
		self.render_finished = []

		self.submit_create = None
		self.present_create = None

		self.submit_list = None

		self.make_sync_objects()

	def make_sync_objects(self):
		semaphore_create = VkSemaphoreCreateInfo(
		    sType=VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO,
		    flags=0)



		self.image_available = vkCreateSemaphore(self.device, semaphore_create, None)
		self.render_finished = vkCreateSemaphore(self.device, semaphore_create, None)

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
		    pSwapchains=[self.swap_chain],
		    pImageIndices=[0],
		    pResults=None)


		# optimization to avoid creating a new array each time
		self.submit_list = ffi.new('VkSubmitInfo[1]', [self.submit_create])

	def cleanup(self):
		vkDestroySemaphore(self.device, self.image_available, None)
		vkDestroySemaphore(self.device, self.render_finished, None)