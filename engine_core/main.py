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

	diskovery.add_class(BigBoy, "BigBoy")
	diskovery.add_class(CubeMan, "CubeMan")

	diskovery.load_scene("template.dk")

	diskovery.run()



if __name__ == '__main__':
	main()
