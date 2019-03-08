import diskovery 
from diskovery_descriptor import BindingType
from diskovery_ubos import *

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
	def __init__(self, position, rotation, scale):
		diskovery.RenderedEntity.__init__(
			self,
			position=position,
			rotation=rotation,
			scale=scale,
			shader_str="Default",
			mesh_str="Default",
			textures_str=["Default"]
		)

	def update(self, ind):
		diskovery.RenderedEntity.update(self, ind)

		self.position.z -= 0.001
		self.position.y += 0.0001
def main():
	diskovery.init(True)

	diskovery.add_mesh("test.obj", "Default")
	diskovery.add_mesh("model.dae", "Man", True)

	diskovery.add_texture("test.png", "Default")
	diskovery.add_texture("character.png", "Man")

	diskovery.add_shader(
		"Default",
		["default.vert", "default.frag"],
		(BindingType.UNIFORM_BUFFER, BindingType.TEXTURE_SAMPLER),
		[MVPMatrix]
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

	diskovery.add_animation("model.dae", "Run")

	cm = CubeMan(
		position=(0, 0, -50),
		rotation=(0, 3.14, 0),
		scale=(16, 9, 10)
	)

	bb = BigBoy(
		position=(0, 4, -10),
		rotation=(0, 0, 0),
		scale=(1, 1, 1)
	)

	diskovery.add_entity(cm, "CubeMan")
	diskovery.add_entity(bb, "Big Boy")

	diskovery.run()

if __name__ == '__main__':
	main()
