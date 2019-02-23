#!/bin/env python

layers = ['VK_LAYER_LUNARG_standard_validation']


from diskovery_instance import DisKovery
from diskovery_vulkan import get_vulkan_command, BindingType, UniformType, MVPMatrix
from diskovery_mesh import Mesh
from diskovery_uniform_buffer import UniformBuffer
from diskovery_shader import Shader
from diskovery_descriptor import make_set_layout
from diskovery_pipeline import Pipeline
from diskovery_descriptor import Descriptor
from diskovery_texture import Texture, make_texture_sampler
from diskovery_entity_manager import EntityManager


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
		shader=None,
		textures=None,
		mesh=None):
		Entity.__init__(self, position)

		self.rotation = rotation if rotation != None else glm.vec3()
		self.scale = scale if scale != None else glm.vec3()

		self.pipeline = shader_definition(shader) if shader != None else shader_definition("Default")
		self.textures = textures if textures != None else ["Default"]
		self.mesh = mesh if mesh != None else None

		self.uniforms = []
		self.descriptor_sets = []

		uniform_types = shader_uniforms(shader)

		for u_type in uniform_types:
			self.uniforms.append(UniformBuffer(u_type))

		self.descriptor = Descriptor(self.pipeline, self.uniforms, self.textures)	

	def update(self, ind):
		m = MVPMatrix()
		m.model = glm.translate(glm.mat4(1.), self.position)
		m.view = glm.lookAt(glm.vec3(2, 2, 2), glm.vec3(), glm.vec3(0, 0, 1))
		m.projection = glm.perspective(
			glm.radians(45.), 
			extent().width/extent().height, 
			0.1, 
			10.
		)
		m.projection[1][1] *= -1

		for uniform in self.uniforms:
			uniform.update(m, ind)


	def cleanup(self):
		for u in uniforms:
			u.cleanup()

		descriptor.cleanup()




_dk = None
_scene = None

_shaders = { }
_descriptors = { }
_pipelines = { }

_meshes = { }
_textures = { }

_samplers = { }

def init():
	global _dk, _scene, _shaders, _pipelines, _descriptors
	pygame.init()
	_dk = DisKovery()
	_dk.fill()
	_scene = EntityManager()

	# Create Pipelines and Descriptors based on all given shaders
	for name, shader in _shaders.items():
		if shader.definition not in _descriptors.keys():
			_descriptors[shader.definition] = make_set_layout(shader.definition)

		_pipelines[shader.definition] = Pipeline(shader, _descriptors[shader.definition])

def run():
	global _dk,  _scene

	# Main loop
	running = True
	if sys.version_info >= (3, 3):
	    clock = time.perf_counter
	else:
	    clock = time.clock

	last_time = clock() * 1000
	fps = 0
	while running:

	    _scene.draw()

	    fps += 1
	    if clock() * 1000 - last_time >= 1000:
	        last_time = clock() * 1000
	        print("FPS: %s" % fps)
	        fps = 0

	    for event in pygame.event.get():
	        if event.type == pygame.QUIT:
	            running = False
	            vkDeviceWaitIdle(_dk.device_manager.logical_device)
	            quit()
	            break

# Helpers that append objects to the environment and/or scene to be referenced
# elsewhere

def add_mesh(filename, name=None):
	global _meshes

	try:
		m = Mesh(filename)
		if name is None:
			_meshes[filename[:-4]] = m
		else:
			_meshes[name] = m
	except:
		print("file '{}' was not able to be loaded as a Mesh!".format(filename))

def add_entity(entity, name):
	global _scene

	if isinstance(entity, Entity):
		_scene[name] = entity
	else:
		print("the given Python object was not a DisKovery Entity.")

def add_shader(name, files, definition, uniforms):
	global _shaders

	try:
		s = Shader(files, definition, uniforms)
		_shaders[name] = s
	except:
		print("One or more of the arguments for shader '{}' are invalid".format(name))

def add_texture(filename, name=None):
	global _textures

	#try:
	t = Texture(filename)
	if name is None:
		_textures[filename[:-4]] = t
	else:
		_textures[name] = t
	#except:
		#print("file '{}' was not able to be loaded as a Texture!".format(filename))

# Helper methods for readability that allow other modules to access Vulkan objects
# that are often necessary, like the logical_device stored in the device_manager,
# rather than having to pass the values in the constructors of the classes and store
# references

def shader_definition(name):
	global _shaders
	return _shaders[name].definition

def shader_uniforms(name):
	global _shaders
	return _shaders[name].uniforms

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

def render_pass():
	global _dk
	return _dk.render_pass

def swap_chain():
	global _dk
	return _dk.swap_chain.swap_chain_ref

def extent():
	global _dk
	return _dk.swap_chain.extent

def descriptor(definition):
	global _descriptors
	return _descriptors[definition]

def pipeline(definition):
	global _pipelines
	print(_pipelines)
	return _pipelines[definition]

def mesh(name):
	global _meshes
	return _meshes[name]

def start_command():
	global _dk
	return _dk.start_command()

def end_command(buff):
	global _dk
	return _dk.end_command(buff)

def dk():
	global _dk
	return _dk

def texture(name):
	global _textures
	return _textures[name]

def texture_sampler(mip):
	global _samplers
	if mip not in _samplers:
		_samplers[mip] = make_texture_sampler(mip)

	return _samplers[mip]

def quit():
	global _dk, _meshes, _scene

	_scene.cleanup()

	for name, mesh in _meshes.items():
		mesh.cleanup()

	for name, dsl in _descriptors.items():
		vkDestroyDescriptorSetLayout(device(), dsl, None)

	for name, pipeline in _pipelines.items():
		pipeline.cleanup()

	for name, tex in _textures.items():
		tex.cleanup()

	_dk.cleanup()
