
import diskovery
from diskovery_ubos import *

class BigBoy(diskovery.RenderedEntity):
	def __init__(self, position, rotation, scale):
		diskovery.RenderedEntity.__init__(
			self,
			position=position,
			rotation=rotation,
			scale=scale,
			shader_str="Default",
			mesh_str="Orb",
			textures_str=["Cube"]
		)

		self.speed = 0.05

	def update(self, ind):
		diskovery.RenderedEntity.update(self, ind)
		self.position.x += diskovery.input("WalkX") *self.speed**2
		self.position.z += diskovery.input("WalkY")*self.speed**2

		if diskovery.input("Spinning"):
			self.rotation.y += self.speed**2;

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
		