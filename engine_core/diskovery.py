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
import math
import pygame
import inspect
import importlib
from ctypes import *

import vk
from diskovery_mesh import Mesh, AnimatedMesh, Animator, Rig
from diskovery_ubos import MVPMatrix, SceneLighting
from diskovery_image import Texture
from diskovery_buffer import UniformBuffer
from diskovery_instance import DkInstance
from diskovery_pipeline import Shader, Pipeline
from diskovery_entity_manager import EntityManager, Renderer
from diskovery_descriptor import make_set_layout, Descriptor
from diskovery_input_manager import InputManager

# Dictionaries and objects wrapped by this module for convenience
_dk = None
_scene = None
_input = None
_camera = None
_classes = { }

_meshes = { }
_textures = { }
_animations = { }

_shaders = { }
_descriptors = { }
_pipelines = { }

_light_scenes = { }

def clear_environment():
	global _meshes, _textures, _animations, _shaders, _descriptors, _pipelines, _light_scenes

	_meshes.clear()
	_textures.clear()
	_animations.clear()
	_shaders.clear()
	_descriptors.clear()
	_pipelines.clear()
	_light_scenes.clear()

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

	a.filename = filename

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

def add_shader(vert, frag, name):
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

	s = Shader([vert, frag])

	_shaders[name] = s

	if s.definition not in _descriptors.keys():
		_descriptors[s.definition] = make_set_layout(_dk, s.definition)

	_pipelines[name] = Pipeline(_dk, s, _descriptors[s.definition], s.animated)

def add_entity(entity, name):
	"""
	Adds an entity to the :class:`~diskovery_entity_manager.EntityManager` stored in this module.

	More details can be found in the :meth:`~diskovery_entity_manager.EntityManager.add_entity` method.

	:param entity: The :class:`~diskovery.Entity` to add
	:param name: A given name to be used as the key for the entity in the :class:`~diskovery_entity_manager.EntityManager`
	"""
	global _scene
	_scene.add_entity(entity, name)

def add_renderer(size=None, bg_color=None):
	global _scene
	if size == None:
		size = _dk.image_data['extent']
	r = Renderer(_dk,
		_dk.image_data['msaa_samples'],
		size=size,
		bg_color=bg_color
	)
	_scene.add_renderer(r)

def add_class(class_type, class_name):
	global _classes

	_classes[class_name] = class_type

def add_light_scene(name):
	global _light_scenes

	scene = SceneLighting()
	_light_scenes[name] = scene

def set_camera_settings(position, rotation, fov, draw_distance, aspect_ratio):
	global _camera

	_camera.position = glm.vec3(position)
	_camera.rotation = glm.vec3(rotation)

	_camera.update_projection(float(fov), float(draw_distance), float(aspect_ratio))


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

def pipeline(name):
	"""
	Retrieve a :class:`~diskovery_pipeline.Pipeline` from the dictionary in this module

	:param name: The definition (key) of the :class:`~diskovery_pipeline.Pipeline`
	"""
	global _pipelines
	return _pipelines[name]

def dimensions():
	"""
	Get the width and height of the screen in pixels.

	:returns: A tuple with the width and height of the screen, in pixels
	"""
	return _dk.image_data['extent'].width, _dk.image_data['extent'].height

def extent():
	return _dk.image_data['extent']

def get_class(name):
	global _classes
	return _classes[name]

def input(name):
	global _input


	if name in _input.input_values.keys():
		return _input.input_values[name]
	else:
		return 0

def entity(name):
	global _scene
	return _scene.entities()[name]

def camera():
	global _camera
	return _camera

def refresh():
	global _scene
	_scene.refresh()

def init(debug_mode=False, config=None, edit_mode=False):
	"""
	Initializes the :class:`~diskovery_instance.DkInstance` and
	:class:`~diskovery_entity_manager.EntityManager` objects used in
	this module.

	:param debug_mode: Whether or not the :class:`~diskovery_instance.DkInstance` should be created with Vulkan Validation Layers
	:param config: An optional dictionary of configuration values to set up the Diskovery instance
	"""
	global _dk, _scene, _camera, _input

	pygame.init()

	_dk = DkInstance(debug_mode)
	_scene = EntityManager(_dk)

	pygame.joystick.init()

	if config != None and 'input' in config:
		_input = InputManager(config['input'])
	else:
		_input = InputManager("maininput.in")

	r = Renderer(_dk, _dk.image_data['msaa_samples'], _dk.sc_image_views, edit_mode)
	_scene.add_renderer(r)

	add_class(Entity, "Entity")
	add_class(RenderedEntity, "RenderedEntity")
	add_class(AnimatedEntity, "AnimatedEntity")
	add_class(Camera, "Camera")
	add_class(Light, "Light")

	custom_module = 'diskovery_entities'

	external_classes = importlib.import_module(custom_module)
	for x in dir(external_classes):
		obj = getattr(external_classes, x)

		if inspect.isclass(obj) and inspect.getmodule(obj).__name__ == custom_module:
			add_class(obj, obj.__name__)

	cam_pos = glm.vec3(0, 0, -5)
	cam_rot = glm.vec3()
	fov = glm.radians(60)
	draw_distance = 1000
	aspect_ratio = 16/9

	if config != None:
		if 'cam_pos' in config:
			cam_pos = glm.vec3(config['cam_pos'])
		if 'cam_rot' in config:
			cam_rot = glm.vec3(config['cam_rot'])
		if 'fov' in config:
			fov = glm.radians(config['fov'])
		if 'draw_distance' in config:
			draw_distance = config['draw_distance']

		if 'width' in config and 'height' in config:
			aspect_ratio = config['width']/config['height']

		if 'bg_color' in config:
			_dk.bg_color = config['bg_color']

	_camera = Camera(cam_pos, cam_rot, fov, draw_distance, aspect_ratio)
	_scene.add_entity(_camera, "Camera")

def draw():
	_scene.draw()

def run():
	"""Begins the game loop and starts the event handler"""
	global _dk, _input, _scene, _light_scenes

	running = True
	while running:
		#for ls in _light_scenes.values():
			#ls.update()
		_scene.draw()
		_input.update()

		for event in pygame.event.get():
			if event.type == pygame.MOUSEBUTTONDOWN:
				if event.button == 4:
					_input.scrollwheel = 1
				if event.button == 5:
					_input.scrollwheel = -1
			if event.type == pygame.QUIT:
				running = False
				_dk.DeviceWaitIdle(_dk.device)
				quit()
				break



def quit():
	"""Handles necessary Vulkan Destroy methods for all Vulkan components"""
	global _dk, _meshes, _textures, _pipelines, _descriptors, _scene

	pygame.joystick.quit()
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
	pygame.quit()

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
	def __init__(self, position=None, rotation=None):
		self.position = glm.vec3(position) if position != None else glm.vec3()
		self.rotation =  glm.vec3(rotation) if rotation != None else glm.vec3()

		self.parent = None
		self.children = []

	presets = NotImplemented

	def world_position(self):
		"""
		Get the position of the :class:`~diskovery.Entity` relative to world coordinates
		rather than the default, which is relative to its parent's coordinates

		:returns: a glm vec3 describing the x, y, and z
			coordinates of the :class:`~diskovery.Entity` in world space
		"""
		p = self.parent
		pos = self.position

		while p != None:
			pos += p.position
			p = p.parent

		return pos

	def update(self, ind):
		pass

	def cleanup(self):
		pass

	def left(self, mat=None):
		if not mat:
			matrix = glm.mat4_cast(glm.quat(self.rotation))
		else:
			matrix = mat

		return glm.vec3(matrix[0])

	def up(self, mat=None):
		if not mat:
			matrix = glm.mat4_cast(glm.quat(self.rotation))
		else:
			matrix = mat

		return glm.vec3(matrix[1])

	def forward(self, mat=None):
		if not mat:
			matrix = glm.mat4_cast(glm.quat(self.rotation))
		else:
			matrix = mat

		return glm.vec3(matrix[2])

	def detach(self):
		"""Removes the reference to the parent of the :class:`~diskovery.Entity` cleanly"""
		self.parent.children.remove(self)
		self.parent = None

	def set_parent(self, parent):
		"""
		Sets the parent of the :class:`~diskovery.Entity` to be the given
		:class:`~diskovery.Entity`

		:param parent: the :class:`~diskovery.Entity` to set the parent as
		"""
		if self.parent != None:
			self.detach()

		self.parent = parent
		parent.children.append(self)

class Camera(Entity):

	presets = { }

	def __init__(self, position, rotation, fov, draw_distance, aspect_ratio):
		Entity.__init__(self, position, rotation)


		self.fov = fov
		self.draw_distance = draw_distance
		self.aspect_ratio = aspect_ratio

		self.cam_speed = 0.04
		self.rot_speed = 0.004

		self.view_matrix = glm.mat4()
		self.proj_matrix = glm.mat4()

		self.update(0)
		self.update_projection()

	def update_projection(self, fov=None, draw_distance=None, aspect_ratio=None):
		if fov != None:
			self.fov = fov
		if draw_distance != None:
			self.draw_distance = draw_distance
		if aspect_ratio != None:
			self.aspect_ratio = aspect_ratio

		self.proj_matrix = glm.perspective(
			self.fov,
			self.aspect_ratio,
			0.1,
			self.draw_distance
		)

	def update(self, ind):
		self.view_matrix = glm.rotate(glm.mat4(1.0), self.rotation.x, glm.vec3(1,0,0)) * \
							glm.rotate(glm.mat4(1.0), self.rotation.y, glm.vec3(0,1,0)) * \
							glm.translate(glm.mat4(1.0), self.position)

		forward = self.forward()
		forward.z *= -1

		up = self.up()
		up.z *= -1

		left = self.left()
		left.z *= -1

		self.position += left * self.cam_speed * input("ObjMoveX") * -0.5
		self.position += forward * self.cam_speed * input("ObjMoveZ") * -0.5
		self.position += up * self.cam_speed * input("ObjMoveY") * -0.25

		if input("Panning"):
			self.position += up * self.cam_speed * input("CamX")
			self.position += left * self.cam_speed * input("CamY")
		if input("Rotating"):
			self.rotation.x -= input("CamRotX") * self.rot_speed
			self.rotation.y += input("CamRotY") * self.rot_speed

		self.position += forward * -3 * input("CamZoom")

		if input("Select"):
			check_selected()

class Light(Entity):

	presets = { }

	def __init__(self, position, direction, tint, intensity, distance, spread, scene):
		Entity.__init__(self, position, direction)

		# To make a directional light (infinite distance), use a value of -1
		self.distance = distance

		self.intensity = intensity
		self.tint = tint

		# To make a point light (infinite spread), use a value of -1
		self.spread = spread

		_light_scenes[scene].lights.append(self)

	def update(self, ind):
		pass

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
	| shader_str        | "Default"         |
	+-------------------+-------------------+
	| textures_str      | ["Default"]       |
	+-------------------+-------------------+
	| mesh_str          | "Default"         |
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
		mesh_str=None,
		textures_str=None,
		light_scene="MainLight"):
		Entity.__init__(self, position, rotation)

		self.scale = glm.vec3(scale) if scale != None else glm.vec3(1, 1, 1)

		self.textures = textures_str if textures_str != None else ["Default"]
		self.mesh = mesh_str if mesh_str != None else None

		self.definition = shader(shader_str).definition if shader_str != None else shader("Default").definition
		self.pipeline = shader_str
		self.uniforms = []

		if light_scene:
			self.light_scene = light_scene

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

		m.model = glm.scale(glm.translate(glm.mat4(1.0), self.position) * \
				  glm.mat4_cast(glm.quat(self.rotation)), self.scale)

		m.view = _camera.view_matrix
		m.projection = _camera.proj_matrix

		self.uniforms[0].update(m.get_data(), ind)

		if hasattr(self, 'light_scene'):
			self.uniforms[1].update(_light_scenes[self.light_scene].get_data(), ind)

	def get_pipeline(self):
		"""
		References the dictionary of pipelines in this module to retrieve
		this :class:`~diskovery.RenderedEntity`'s pipeline

		:returns: The :class:`~diskovery_pipeline.Pipeline` with this :class:`~diskovery.RenderedEntity`'s definition
		"""
		return pipeline(self.pipeline)

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
		mesh_str=None,
		textures_str=None,
		animations_str=None,
		light_scene="MainLight"
		):
		RenderedEntity.__init__(self, position, rotation, scale, shader_str, mesh_str, textures_str, light_scene)

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

		RenderedEntity.update(self, ind)

		self.animator.update()
		if hasattr(self, 'light_scene'):
			self.uniforms[2].update(self.rig.get_joint_data(), ind)
		else:
			self.uniforms[1].update(self.rig.get_joint_data(), ind)

def _save_scene(filename, scene_name):
	global _meshes, _textures, _shaders, _animations, _scene

	contents = "{}\n".format(scene_name)

	f = open(filename, "w+")

	contents += "Meshes\n"
	for name, m in _meshes.items():
		animated = isinstance(m, AnimatedMesh)
		contents += "{} {} {}\n".format(m.filename, name, 'T' if animated else 'F')

	contents += "Textures\n"
	for name, t in _textures.items():
		contents += "{} {}\n".format(t.filename, name)

	contents += "Shaders\n"
	for name, s in _shaders.items():
		contents += "{} {} {}\n".format(s.sources[0], s.sources[1], name)

	contents += "Animations\n"
	for name, a in _animations.items():
		contents += "{} {}\n".format(a.filename, name)

	contents += "Entities\n"
	for name, e in _scene.entities().items():
		contents += "E {} {}\n".format(e.__class__.__name__, name)
		args = dict(inspect.getmembers(e.__class__.__init__.__code__))['co_varnames']
		for arg_name in args:
			if arg_name == "self":
				continue

			attr = getattr(e, arg_name)

			if type(attr) == glm.vec3:
				attr = "{} {} {}".format(attr.x, attr.y, attr.z)
			contents += "{}\n".format(attr)

	f.write(contents)

	f.close()

def check_selected():
	m_pos = pygame.mouse.get_pos()

	pixel_data = _scene.get_image(0, 1)
	dim = (_dk.image_data['extent'].width, _dk.image_data['extent'].height)

	surface = pygame.Surface((dim[0], dim[1]))

	for i in range(0, dim[1]):
		for j in range(0, dim[0]):
			offset = (i * dim[0] + j) * 4
			pixel = pixel_data[offset:(offset + 4)]
			color = pygame.Color(pixel[0], pixel[1], pixel[2], pixel[3])
			surface.set_at((j, i), color)

	#print(surface.get_at(m_pos))

	pygame.image.save(surface, "test_img.png")
