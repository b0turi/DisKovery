
import diskovery
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

		self.speed = 0.05

	def update(self, ind):
		diskovery.AnimatedEntity.update(self, ind)

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
		self.position.x += diskovery.input("WalkX")
		self.position.y += diskovery.input("WalkY")
