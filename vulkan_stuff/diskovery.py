#!/bin/env python

layers = ['VK_LAYER_LUNARG_standard_validation']


from diskovery_instance import DisKovery
from diskovery_vulkan import get_vulkan_command
from diskovery_mesh import Mesh

import pygame
from vulkan import *

import os
import time

import glm

class Entity():
	def __init__(self, position=None):
		self.position = position if position != None else glm.vec3()

		self.parent = None
		self.children = []

	def world_position(self):
		p = self.parent
		pos = self.position

		while p != None:
			pos += p.position
			p = p.parent

		return pos

	def detach(self):
		self.parent.children.remove(self)
		self.parent = None

	def set_parent(self, parent):
		if self.parent != None:
			self.detach()

		self.parent = parent
		parent.children.append(self)

class RenderedEntity(Entity):
	def __init__(self, 
		position=None, 
		rotation=None, 
		scale=None, 
		pipeline=None,
		textures=None,
		mesh=None):
		Entity.__init__(self, position)

		self.rotation = rotation if rotation != None else glm.vec3()
		self.scale = scale if scale != None else glm.vec3()

		self.pipeline = pipeline if pipeline != None else "Default"
		self.textures = textures if textures != None else ["Default"]
		self.mesh = mesh if mesh != None else None

_dk = None

_scene = {}

_shaders = {}
_descriptors = {}
_pipelines = {}

_meshes = {}
_textures = {}

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

# Helpers that append objects to the environment and/or scene to be referenced
# elsewhere

def add_mesh(filename):
	global _meshes

	try:
		m = Mesh(filename)
		_meshes[filename[:-4]] = m
	except:
		print("file '{}' was not able to be loaded as a Mesh!".format(filename))

def add_entity(entity, name):
	global _scene

	if isinstance(entity, Entity):
		_scene[name] = entity
	else:
		print("the given Python object was not a DisKovery Entity.")

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

def framebuffers():
	global _dk
	return _dk.framebuffers

def framebuffer(index):
	global _dk
	return _dk.framebuffers[index]

def extent():
	global _dk
	return _dk.swap_chain.extent

def quit():
	global _dk, _meshes
	for name, mesh in _meshes.items():
		mesh.cleanup()
	_dk.cleanup()
