#!/bin/env python

layers = ['VK_LAYER_LUNARG_standard_validation']


from diskovery_instance import DisKovery
from diskovery_vulkan import get_vulkan_command

import pygame
from vulkan import *

import os
import time

_dk = None

def init():
	global _dk
	pygame.init()
	_dk = DisKovery()

def run():
	global _dk
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

	    _dk.draw_frame()
	    for event in pygame.event.get():
	        if event.type == pygame.QUIT:
	            running = False
	            vkDeviceWaitIdle(_dk.device_manager.logical_device)
	            quit()
	            break

# Helper methods for readability that allow other modules to access Vulkan objects
# that are often necessary, like the logical_device stored in the device_manager,
# rather than having to pass the values in the constructors of the classes and store
# references

def instance():
	global _dk
	return _dk.window.instance

def surface():
	global _dk
	return _dk.window.surface

def device_manager():
	global _dk
	return _dk.device_manager

def physical_device():
	global _dk
	return _dk.device_manager.physical_device

def device():
	global _dk
	return _dk.device_manager.logical_device

def graphics_queue():
	global _dk
	return _dk.device_manager.graphics_queue["queue"]

def present_queue():
	global _dk
	return _dk.device_manager.present_queue["queue"]

def pool():
	global _dk
	return _dk.command_pool

def num_back_buffers():
	global _dk
	return len(_dk.framebuffers)



def quit():
	global _dk
	_dk.cleanup()
