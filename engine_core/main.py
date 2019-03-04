import diskovery
from diskovery_descriptor import BindingType
from diskovery_ubos import *
def main():
	diskovery.init(True)

	diskovery.add_mesh("model.dae", "Default", True)
	diskovery.add_animation("model.dae", "Run")
	diskovery.add_texture("character.png", "Default")
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

	ae = diskovery.AnimatedEntity(
		position=(0, 4, -10),
		shader_str="Animated",
		textures_str=["Default"],
		mesh_str="Default",
		animations_str=["Run"]
	)

	diskovery.add_entity(ae, "Big Boy")

	diskovery.run()

if __name__ == '__main__':
	main()
