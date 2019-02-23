#!/bin/env python


import diskovery
from diskovery_vulkan import BindingType, UniformType
import glm

def main():

	diskovery.add_shader( 
		"Default",
		["default-v.vert", "default-f.frag"],
		( BindingType.TEXTURE_SAMPLER, 
		  BindingType.UNIFORM_BUFFER ),
		[UniformType.MVP_MATRIX]
	)

	diskovery.init()
	

	diskovery.add_mesh("test.obj", "Cube")
	diskovery.add_texture("test.png", "Default")

	# Create a test object using the assets defined above

	cube = diskovery.RenderedEntity(
		position=glm.vec3(0, 0, 0),
		rotation=glm.vec3(0, 0, 0),
		scale=glm.vec3(1, 1, 1),
		shader="Default",
		textures=["Default"],
		mesh="Cube"
	)

	diskovery._scene.add_entity("Ya boi", cube)


	diskovery.run()
if __name__ == "__main__":
	main()