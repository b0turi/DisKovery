import diskovery 
from diskovery_descriptor import BindingType
from diskovery_ubos import *
from diskovery_entity_manager import Renderer

class BigBoy(diskovery.AnimatedEntity):
	def __init__(self, position, rotation, scale):
		diskovery.AnimatedEntity.__init__(
			self,
			position=position,
			rotation=rotation,
			scale=scale,
			shader_str="Animated",
			mesh_str="Man",
			textures_str=["Man"],
			animations_str=["Run"]
		)

	def update(self, ind):
		diskovery.AnimatedEntity.update(self, ind)

		self.position.x += 0.0001
		self.rotation.y += 0.0005

class CubeMan(diskovery.RenderedEntity):
	def __init__(self, position, rotation, scale, color):
		diskovery.RenderedEntity.__init__(
			self,
			position=position,
			rotation=rotation,
			scale=scale,
			shader_str="GUI",
			mesh_str="Default",
			textures_str=["Default"]
		)

		self.color = color

	def update(self, ind):
		diskovery.RenderedEntity.update(self, ind)
		dim = diskovery.dimensions()
		s = ScreenSize(dim[0], dim[1])
		self.uniforms[1].update(s.get_data(), ind)

def main():
	diskovery.init(True)

	diskovery.add_mesh("test.obj", "Default")
	diskovery.add_mesh("model.dae", "Man", True)

	diskovery.add_texture("test.png", "Default")
	diskovery.add_texture("character.png", "Man")

	diskovery.add_shader(
		"Color Picker",
		["color_pick.vert", "color_pick.frag"],
		(BindingType.UNIFORM_BUFFER, 
		BindingType.UNIFORM_BUFFER,
		BindingType.UNIFORM_BUFFER,
		BindingType.UNIFORM_BUFFER),
		[MVPMatrix, ObjectColor, ScreenSize, Boolean]
	)

	diskovery.add_shader(
		"Animated",
		["animated.vert", "default.frag"],
		(BindingType.UNIFORM_BUFFER,
		BindingType.TEXTURE_SAMPLER,
		BindingType.UNIFORM_BUFFER),
		[MVPMatrix, JointData],
		True
	)

	diskovery.add_shader(
		"Default",
		["default.vert", "default.frag"],
		(BindingType.UNIFORM_BUFFER, BindingType.TEXTURE_SAMPLER),
		[MVPMatrix]
	)

	diskovery.add_shader(
		"GUI",
		["gui.vert", "gui.frag"],
		(BindingType.UNIFORM_BUFFER, 
		BindingType.TEXTURE_SAMPLER,
		BindingType.UNIFORM_BUFFER),
		[MVPMatrix, ScreenSize]
	)

	diskovery.add_animation("model.dae", "Run")

	for i in range(0, 10):
		cm = CubeMan(
			position=(i*80 + 10, 10, 0),
			rotation=(0, 0, 0),
			scale=(60, 60, 60),
			color=hex(i*10+1)
		)

		diskovery.add_entity(cm, "CubeMan{}".format(i))

	bb = BigBoy(
		position=(0, 4, -10),
		rotation=(0, 0, 0),
		scale=(1, 1, 1)
	)

	diskovery.add_entity(bb, "big")

	print(diskovery.dimensions())

	diskovery.run()

if __name__ == '__main__':
	main()
