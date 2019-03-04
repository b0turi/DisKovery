#!/bin/env/python

"""
The :mod:`diskovery` module is the primary module that acts as a wrapper
around the functionality of the other DisKovery submodules. It stores
dictionaries that handle the memory management of assets and objects
to be used in the scene, including:

- :class:`~diskovery_mesh.Mesh` objects for 3D models
- :class:`~diskovery_image.Texture` objects for external images
- :class:`~diskovery_pipeline.Shader` objects for GLSL shader programs
- :class:`~diskovery_pipeline.Pipeline` objects (associated with :class:`~diskovery_pipeline.Shader` objects)
- VkDescriptorSetLayout_ objects (associated with :class:`~diskovery_pipeline.Shader` objects)
- VkSampler_ objects (for sampling :class:`~diskovery_image.Texture` objects)

.. _VkDescriptorSetLayout: https://www.khronos.org/registry/vulkan/specs/1.1-extensions/man/html/VkDescriptorSetLayout.html
.. _VkSampler: https://www.khronos.org/registry/vulkan/specs/1.1-extensions/man/html/VkSampler.html

In addition to managing assets, it stores objects of a few other classes:

- A :class:`~diskovery_instance.DkInstance` that is used by all DisKovery objects that interface with Vulkan
- A :class:`~diskovery_entity_manager.EntityManager` that stores all :class:`~diskovery.Entity` objects in the scene

The :mod:`diskovery` module also holds the definitions for the three basic
entity types, from which DisKovery users can extend their own custom object definitions:

- :class:`~diskovery.Entity` - a basic Entity that has a position in the 3D world
- :class:`~diskovery.RenderedEntity` - an :class:`~diskovery.Entity` with a :class:`~diskovery.Mesh` that is rendered to the scene
- :class:`~diskovery.AnimatedEntity` - a :class:`~diskovery.RenderedEntity` with an :class:`~diskovery_animator.Animator` to handle skeletal animation
"""
import glm
import pygame

from diskovery_mesh import Mesh, AnimatedMesh, Animator, Rig
from diskovery_ubos import MVPMatrix
from diskovery_image import Texture
from diskovery_buffer import UniformBuffer
from diskovery_instance import DkInstance
from diskovery_pipeline import Shader, Pipeline
from diskovery_entity_manager import EntityManager
from diskovery_descriptor import make_set_layout, Descriptor

# Dictionaries and objects wrapped by this module for convenience
_dk = None
_scene = None

_meshes = { }
_textures = { }
_animations = { }

_shaders = { }
_descriptors = { }
_pipelines = { }

_samplers = { }

def add_mesh(filename, name=None, animated=False):
	"""
	Creates and adds a :class:`~diskovery_mesh.Mesh` to the dictionary
	of Meshes stored in this module. Has some basic wrapping to ensure
	keys are not duplicated and the filename provided links to a valid
	3D object data file.

	:param filename: A str of the name of a file stored locally that contains 3D object data (either .obj or .dae format)
	:param name: A given name for the newly created mesh. If not defined, the filename without its extension will be the key used in the dictionary
	"""
	global _meshes

	if not animated:
		m = Mesh(_dk, filename)
	else:
		m = AnimatedMesh(_dk, filename, True, False)

	if name is None:
		_meshes[filename[:-4]] = m
	else:
		_meshes[name] = m

def add_animation(filename, name=None):
	global _animations

	a = AnimatedMesh(_dk, filename, True, True).anim

	if name is None:
		_animations[filename[:-4]] = a
	else:
		_animations[name] = a

def add_texture(filename, name=None):
	"""
	Creates and adds a :class:`~diskovery_image.Texture` to the dictionary
	of Textures stored in this module. Has some basic wrapping to ensure
	keys are not duplicated and the filename provided links to a valid
	image file.

	:param filename: A str of the name of a file stored locally that contains image data (all common formats accepted)
	:param name: A given name for the newly created texture. If not defined, the filename without its extension will be the key used in the dictionary
	"""
	global _textures

	t = Texture(_dk, filename)
	if name is None:
		_textures[filename[:-4]] = t
	else:
		_textures[name] = t

def add_shader(name, files, definition, uniforms, animated=False):
	"""
	Creates and adds a :class:`~diskovery_pipeline.Shader` to the dictionary
	of Shaders stored in this module. Also creates a :class:`~diskovery_pipeline.Pipeline`
	and VkDescriptorSetLayout_ based on the definition given and adds them to their
	respective dictionaries.

	:param name: A given name for the newly created shader
	:param files: A list containing the filenames of all stages of the shader (for now, just vertex and fragment shaders)
	:param definition: A tuple of :class:`~diskovery_descriptor.BindingType` objects that reflect the bindings used in the shader
	:param uniforms: A list of :class:`~diskovery_descriptor.UniformType` objects that reflect the content of each of the above bindings that binds a uniform
	"""
	global _shaders

	s = Shader(files, definition, uniforms)

	_shaders[name] = s

	if s.definition not in _descriptors.keys():
		_descriptors[definition] = make_set_layout(_dk, definition)

	_pipelines[definition] = Pipeline(_dk, s, _descriptors[definition], animated)

def add_entity(entity, name):
	"""
	Adds an entity to the :class:`~diskovery_entity_manager.EntityManager` stored in this module.

	More details can be found in the :meth:`~diskovery_entity_manager.EntityManager.add_entity` method.

	:param entity: The :class:`~diskovery.Entity` to add
	:param name: A given name to be used as the key for the entity in the :class:`~diskovery_entity_manager.EntityManager`
	"""
	global _scene
	_scene.add_entity(entity, name)

def mesh(name):
	"""
	Retrieve a :class:`~diskovery_mesh.Mesh` from the dictionary in this module

	:param name: The name (key) of the :class:`~diskovery_mesh.Mesh`
	"""
	global _meshes
	return _meshes[name]

def texture(name):
	"""
	Retrieve a :class:`~diskovery_image.Texture` from the dictionary in this module

	:param name: The name (key) of the :class:`~diskovery_image.Texture`
	"""
	global _textures
	return _textures[name]

def shader(name):
	"""
	Retrieve a :class:`~diskovery_pipeline.Shader` from the dictionary in this module

	:param name: The name (key) of the :class:`~diskovery_pipeline.Shader`
	"""
	global _shaders
	return _shaders[name]

def descriptor(definition):
	"""
	Retrieve a VkDescriptorSetLayout_ from the dictionary in this module

	:param definition: The definition (key) of the VkDescriptorSetLayout_
	"""
	global _descriptors
	return _descriptors[definition]

def pipeline(definition):
	"""
	Retrieve a :class:`~diskovery_pipeline.Pipeline` from the dictionary in this module

	:param name: The definition (key) of the :class:`~diskovery_pipeline.Pipeline`
	"""
	global _pipelines
	return _pipelines[definition]

def init(debug_mode=False):
	"""
	Initializes the :class:`~diskovery_instance.DkInstance` and
	:class:`~diskovery_entity_manager.EntityManager` objects used in
	this module.

	:param debug_mode: Whether or not the :class:`~diskovery_instance.DkInstance` should be created with Vulkan Validation Layers
	"""
	global _dk, _scene
	_dk = DkInstance(debug_mode)
	_scene = EntityManager(_dk)

def run():
	"""Begins the game loop and starts the event handler"""
	global _dk

	running = True
	while running:

		_scene.draw()

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
				_dk.DeviceWaitIdle(_dk.device)
				quit()
				break

def quit():
	"""Handles necessary Vulkan Destroy methods for all Vulkan components"""
	global _dk, _meshes, _textures, _pipelines, _descriptors, _scene

	_scene.cleanup()

	for mesh in _meshes.values():
		mesh.cleanup()

	for texture in _textures.values():
		texture.cleanup()

	for pipeline in _pipelines.values():
		pipeline.cleanup()

	for descriptor in _descriptors.values():
		_dk.DestroyDescriptorSetLayout(_dk.device, descriptor, None)

	_dk.cleanup()

class Entity():
	"""
	The :class:`~diskovery.Entity` class is the simplest object that can be added to the game world.
	An :class:`~diskovery.Entity` exists in 3D space, but will not have any visual representation in
	the game world.

	Multiple default extensions of the :class:`~diskovery.Entity` class are included in DisKovery, namely:
	- :class:`~diskovery_defaults.Light` for handling the lighting of a scene
	- :class:`~diskovery_defaults.Camera` for setting the view of the scene

	**Attributes of the Entity class:**

	.. py:attribute:: position

		The position of the :class:`~diskovery.Entity` as a 3D vector, stored as a tuple.
		Stores the value of :attr:`diskovery.Entity.position` if one was provided.

	.. py:attribute:: parent

		A reference to another :class:`~diskovery.Entity` that, when not set to ``None``,
		gives a parent position from which the position of this :class:`~diskovery.Entity`
		is translated so that the position of this Entity is relative to its parent

	.. py:attribute:: children

		A list of references to other :class:`~diskovery.Entity` objects, for use as
		described in the parent attribute's description.

	**Methods of the Entity class:**
	"""
	def __init__(self, position=None):
		self.position = position if position != None else (0, 0, 0)

		self.parent = None
		self.children = []

	def world_position(self):
		"""
		Get the position of the :class:`~diskovery.Entity` relative to world coordinates
		rather than the default, which is relative to its parent's coordinates

		:returns: a tuple describing the x, y, and z coordinates of the :class:`~diskovery.Entity` in world space
		"""
		p = self.parent
		pos = self.position

		while p != None:
			pos = vec_add(pos, p.position)
			p = p.parent

		return pos

	def detach(self):
		"""Removes the reference to the parent of the :class:`~diskovery.Entity` cleanly"""
		self.parent.children.remove(self)
		self.parent = None

	def set_parent(self, parent):
		"""
		Sets the parent of the :class:`~diskovery.Entity` to be the given :class:`~diskovery.Entity`

		:param parent: the :class:`~diskovery.Entity` to set the parent as
		"""
		if self.parent != None:
			self.detach()

		self.parent = parent
		parent.children.append(self)

class RenderedEntity(Entity):
	"""
	Extends :class:`~diskovery.Entity` to include references to the necessary objects
	to present an object on the screen. All parameters are optional, as default values
	for each are either preloaded into the environment or simple tuples:

	+-------------------+-------------------+
	| parameter         | default value     |
	+===================+===================+
	| position          | (0, 0, 0)         |
	+-------------------+-------------------+
	| rotation          | (0, 0, 0)         |
	+-------------------+-------------------+
	| scale             | (1, 1, 1)         |
	+-------------------+-------------------+
	| shade             | "Default"         |
	+-------------------+-------------------+
	| textures          | ["Default"]       |
	+-------------------+-------------------+
	| mesh              | "Default"         |
	+-------------------+-------------------+

	**Attributes of the RenderedEntity class:**

	.. py:attribute:: rotation

		The rotation of the :class:`~diskovery.RenderedEntity` as a
		set of Euler angles, stored as a tuple.

	.. py:attribute:: scale

		The x, y, and z scale of the :class:`~diskovery.RenderedEntity`, stored as a tuple

	.. py:attribute:: textures

		A list of strings containing keys to the dictionary of
		:class:`~diskovery_image.Texture` objects stored in this module

	.. py:attribute:: mesh

		A string containing a key to the dictionary of
		:class:`~diskovery_mesh.Mesh` objects stored in this module

	.. py:attribute:: definition

		A tuple of :class:`~diskovery_descriptor.BindingType` s that is used to determine
		which VkDescriptorSetLayout_ is needed. Taken from the :class:`~diskovery_pipeline.Shader`
		given by the ``shade`` argument, or the default shader if no value is given.

	.. py:attribute:: uniforms

		A list of :class:`~diskovery_buffer.UniformBuffer` objects filled by
		iterating over the list of :class:`~diskovery_descriptor.UniformType` s
		stored in the :class:`~diskovery_pipeline.Shader` object

	.. py:attribute:: descriptor

		A :class:`~diskovery_descriptor.Descriptor` defined by the definition described above,
		the VkDescriptorSetLayout_ associated with that definition (in this module's dictionary
		of descriptor set layouts, using the definition tuple as a key)

	"""
	global _dk

	def __init__(self,
		position=None,
		rotation=None,
		scale=None,
		shader_str=None,
		textures_str=None,
		mesh_str=None):
		Entity.__init__(self, position)

		self.rotation = rotation if rotation != None else (0, 0, 0)
		self.scale = scale if scale != None else (1, 1, 1)

		self.textures = textures_str if textures_str != None else ["Default"]
		self.mesh = mesh_str if mesh_str != None else None

		self.definition = shader(shader_str).definition if shader_str != None else shader("Default").definition
		self.uniforms = []

		self.rot=3.14/4 * 3

		uniform_types = shader(shader_str).uniforms
		for u_type in uniform_types:
			self.uniforms.append(UniformBuffer(_dk, u_type))

		if len(self.definition) > 0:
			self.descriptor = Descriptor(
				_dk,
				self.definition,
				descriptor(self.definition),
				self.uniforms,
				[texture(t) for t in self.textures]
			)

	def update(self, ind):
		"""
		Updates every :class:`~diskovery_buffer.UniformBuffer` stored in
		``uniforms`` with new data

		:param ind: the index indicating which :class:`~diskovery_buffer.Buffer` in each :class:`~diskovery_buffer.UniformBuffer` should be filled with new data
		"""
		m = MVPMatrix()

		m.model = glm.rotate(
			glm.translate(glm.mat4(1.0), glm.vec3(self.position)),
			self.rot,
			glm.vec3(0, 1, 0)
		)

		m.view = glm.translate(glm.mat4(1.0), glm.vec3(0, 0, -5))
		m.projection = glm.perspective(
			glm.radians(90),
			_dk.image_data['extent'].width / _dk.image_data['extent'].height,
			0.1,
			10000.
		)

		for uniform in self.uniforms:
			uniform.update(m.get_data(), ind)

		self.rot += 0.0001
		if self.rot > 6.2832:
			self.rot = 0

	def get_pipeline(self):
		"""
		References the dictionary of pipelines in this module to retrieve
		this :class:`~diskovery.RenderedEntity`'s pipeline

		:returns: The :class:`~diskovery_pipeline.Pipeline` with this :class:`~diskovery.RenderedEntity`'s definition
		"""
		return pipeline(self.definition)

	def get_mesh(self):
		"""
		References the dictionary of meshes in this module to retrieve
		this :class:`~diskovery.RenderedEntity`'s mesh

		:returns: The :class:`~diskovery_mesh.Mesh` with this :class:`~diskovery.RenderedEntity`'s key
		"""
		return mesh(self.mesh)

	def get_texture(self, index):
		"""
		References the dictionary of textures in this module to retrieve
		this :class:`~diskovery.RenderedEntity`'s texture at a given index
		in its list of textures

		:param index: The index in the list of textures to reference when retrieving a texture

		:returns: The :class:`~diskovery_image.Texture` with the key at the given index of this :class:`~diskovery.RenderedEntity`'s key list
		"""
		return texture(self.textures[index])

	def cleanup(self):
		"""
		Handles necessary Destroy methods for all the Vulkan components
		contained inside the :class:`~diskovery.RenderedEntity`
		"""
		for u in self.uniforms:
			u.cleanup()

		if hasattr(self, "descriptor"):
			self.descriptor.cleanup()

class AnimatedEntity(RenderedEntity):
	def __init__(self,
		position=None,
		rotation=None,
		scale=None,
		shader_str=None,
		textures_str=None,
		mesh_str=None,
		animations_str=None
		):
		RenderedEntity.__init__(self, position, rotation, scale, shader_str, textures_str, mesh_str)

		self.animations = animations_str if animations_str != None else []
		self.rig = Rig.from_template(mesh(mesh_str).rig)

		self.animator = Animator(_scene, _animations, self, self.animations)
		if len(self.animations) > 0:
			self.animator.play(self.animations[0])


	def update(self, ind):
		"""
		Updates every :class:`~diskovery_buffer.UniformBuffer` stored in
		``uniforms`` with new data

		:param ind: the index indicating which :class:`~diskovery_buffer.Buffer` in each :class:`~diskovery_buffer.UniformBuffer` should be filled with new data
		"""
		m = MVPMatrix()

		m.model = glm.rotate(
			glm.translate(glm.mat4(1.0), glm.vec3(self.position)),
			self.rot,
			glm.vec3(0, 1, 0)
		)

		m.view = glm.translate(glm.mat4(1.0), glm.vec3(0, 0, -5))
		m.projection = glm.perspective(
			glm.radians(60),
			_dk.image_data['extent'].width / _dk.image_data['extent'].height,
			0.1,
			10000.
		)

		self.uniforms[0].update(m.get_data(), ind)
		self.animator.update()
		self.uniforms[1].update(self.rig.get_joint_data(), ind)


		if self.rot > 6.2832:
			self.rot = 0
