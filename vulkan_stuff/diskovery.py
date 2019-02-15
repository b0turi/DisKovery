#!/bin/env python

layers = ['VK_LAYER_LUNARG_standard_validation']

from diskovery_window import DiskoveryWindow
from diskovery_device_manager import DeviceManager
from diskovery_swap_chain import SwapChain
from diskovery_vulkan import *
from diskovery_pipeline import Pipeline
from diskovery_command_buffer import *
from diskovery_sync_objects import SyncObjects

from vulkan import *
from sdl2 import *
from sdl2.ext import *

import os
import time

def getVulkanCommand(instance, cmd):
	return vkGetInstanceProcAddr(instance, cmd)

window = None
device_manager = None
swap_chain = None
render_pass = None
pipeline = None
framebuffers = None
command_pool = None
command_buffers = None
sync = None

def draw_frame():
	global window, device_manager, swap_chain, command_buffers, sync
	try:
	    image_index = getVulkanCommand(window.instance, "vkAcquireNextImageKHR")(
	    	device_manager.logical_device, swap_chain.swap_chain_ref, UINT64_MAX, 
	       	sync.image_available, None)
	except VkNotReady:
	    print('not ready')
	    return

	sync.submit_create.pCommandBuffers[0] = command_buffers.buffers[image_index]
	vkQueueSubmit(device_manager.graphics_queue["queue"], 1, sync.submit_list, None)

	sync.present_create.pImageIndices[0] = image_index
	getVulkanCommand(window.instance, "vkQueuePresentKHR")(device_manager.present_queue["queue"], 
		sync.present_create)

def Diskovery_init():
	global window, device_manager, swap_chain, command_buffers, sync, render_pass, command_pool, pipeline, framebuffers
	# Make sure SDL is supported
	if SDL_Init(SDL_INIT_VIDEO | SDL_INIT_EVENTS) != 0:
		raise Exception(SDL_GetError())

	window = DiskoveryWindow(800, 600)
	device_manager = DeviceManager(window)
	swap_chain = SwapChain(window, device_manager)

	extent = swap_chain.extent

	render_pass = make_render_pass(swap_chain.surface_format, device_manager.logical_device)
	pipeline = Pipeline(device_manager, render_pass, extent)

	framebuffers = make_frame_buffers(swap_chain.image_views, render_pass, 
										extent, device_manager.logical_device)

	command_pool = make_command_pool(device_manager.logical_device, 
									 device_manager.graphics_queue["index"])

	command_buffers = CommandBuffer(command_pool, device_manager.logical_device,
			framebuffers, render_pass, extent, pipeline.pipeline_ref)

	sync = SyncObjects(device_manager.logical_device, 
		command_buffers.buffers, swap_chain.swap_chain_ref)


def Diskovery_run():
	global device_manager
	# Main loop
	running = True
	if sys.version_info >= (3, 3):
	    clock = time.perf_counter
	else:
	    clock = time.clock

	last_time = clock() * 1000
	fps = 0
	while running:
	    fps += 1
	    if clock() * 1000 - last_time >= 1000:
	        last_time = clock() * 1000
	        print("FPS: %s" % fps)
	        fps = 0

	    events = get_events()
	    draw_frame()
	    for event in events:
	        if event.type == SDL_QUIT:
	            running = False
	            vkDeviceWaitIdle(device_manager.logical_device)
	            Diskovery_exit()
	            break
	

def Diskovery_exit():
	global sync, device_manager, framebuffers, command_pool, pipeline, render_pass, swap_chain, window
	sync.cleanup()
	destroy_frame_buffers(device_manager.logical_device, framebuffers)
	destroy_command_pool(device_manager.logical_device, command_pool)
	pipeline.cleanup()
	destroy_render_pass(device_manager.logical_device, render_pass)
	swap_chain.cleanup()
	device_manager.cleanup()
	window.cleanup()