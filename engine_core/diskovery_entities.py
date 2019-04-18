import glm
import math
import diskovery
from diskovery_ubos import *
import diskovery_scene_manager

""" Classes used in the Level Editor """

class SelectableEntity(diskovery.RenderedEntity):
	def __init__(self, 
		position=None, 
		rotation=None, 
		scale=None, 
		mesh_str="Cube", 
		textures_str=["Blank"],
		light_scene="MainLight", 
		color=0,
		name=None,
		tint=(1, 1, 1, 1),
		is_lit=True,
		selected = False,
		chi = None):
		diskovery.RenderedEntity.__init__(
			self,
			position=position,
			rotation=rotation,
			scale=scale,
			shader_str="Selection",
			mesh_str=mesh_str,
			textures_str=textures_str,
			light_scene=light_scene
		)

		hex_val = str(hex(color))[2:]
		if len(hex_val) <= 2:
			self.color = (0, 0, int(hex_val, 16)/255, 1)
		elif len(hex_val) <= 4:
			self.color = (0, int(hex_val[:2], 16)/255, int(hex_val[2:], 16)/255, 1)
		elif len(hex_val) > 4:
			self.color = (int(hex_val[:2], 16)/255, int(hex_val[2:4], 16)/255, int(hex_val[4:], 16)/255, 1)

		self.tint = tint
		self.is_lit = is_lit
		self.selected = selected

		self.name = name

		self.speed = 30

		self.chi = chi

	def update(self, ind):
		diskovery.RenderedEntity.update(self, ind)

		lit = Boolean(self.is_lit)
		self.uniforms[2].update(lit.get_data(), ind)

		tint = Tint(self.tint)
		self.uniforms[3].update(tint.get_data(), ind)

		selected = Boolean(self.selected)
		self.uniforms[4].update(selected.get_data(), ind)


		col = Color(self.color)
		self.uniforms[5].update(col.get_data(), ind)

		if self.selected:
			diskovery.entity("Cursor").show()
			diskovery.entity("Cursor").position = self.position
			diskovery.entity("Cursor").rotation = self.rotation

			self.position += self.left() * self.speed * diskovery.input("ObjMoveX") * diskovery.frame_time()
			self.position += -self.forward() * self.speed * diskovery.input("ObjMoveZ")* diskovery.frame_time()
			self.position += -self.up() * self.speed * diskovery.input("ObjMoveY")* diskovery.frame_time()

			if self.chi != None:
				diskovery.entity(self.chi).position = self.position
				diskovery.entity(self.chi).rotation = self.rotation
			
			diskovery_scene_manager.update_config(self, self.name, 'position')

class SelectableTerrain(diskovery.Terrain):
	def __init__(self, 
		position=None,
		size=None,
		sub=None,
		amp=None,
		heightmap=None,
		name=None,
		textures_str=None, 
		color=0,
		tint=(1, 1, 1, 1),
		is_lit=True,
		selected = False,
		chi = None):
		diskovery.Terrain.__init__(
			self,
			position=position,
			size=size,
			sub=sub,
			amp=amp,
			heightmap=heightmap,
			name=name,
			textures_str=textures_str
		)

		hex_val = str(hex(color))[2:]
		if len(hex_val) <= 2:
			self.color = (0, 0, int(hex_val, 16)/255, 1)
		elif len(hex_val) <= 4:
			self.color = (0, int(hex_val[:2], 16)/255, int(hex_val[2:], 16)/255, 1)
		elif len(hex_val) > 4:
			self.color = (int(hex_val[:2], 16)/255, int(hex_val[2:4], 16)/255, int(hex_val[4:], 16)/255, 1)

		self.tint = tint
		self.is_lit = is_lit
		self.selected = selected

		self.speed = 30

		self.chi = chi

	def update(self, ind):
		diskovery.RenderedEntity.update(self, ind)

		lit = Boolean(self.is_lit)
		self.uniforms[2].update(lit.get_data(), ind)

		tint = Tint(self.tint)
		self.uniforms[3].update(tint.get_data(), ind)

		selected = Boolean(self.selected)
		self.uniforms[4].update(selected.get_data(), ind)

		col = Color(self.color)
		self.uniforms[5].update(col.get_data(), ind)

		sub = Float(self.sub)
		self.uniforms[6].update(sub.get_data(), ind)

		if self.selected:
			diskovery.entity("Cursor").show()
			diskovery.entity("Cursor").position = self.position
			diskovery.entity("Cursor").rotation = self.rotation

			self.position += self.left() * self.speed * diskovery.input("ObjMoveX") * diskovery.frame_time()
			self.position += -self.forward() * self.speed * diskovery.input("ObjMoveZ") * diskovery.frame_time()
			self.position += -self.up() * self.speed * diskovery.input("ObjMoveY") * diskovery.frame_time()

			if self.chi != None:
				diskovery.entity(self.chi).position = self.position
				diskovery.entity(self.chi).rotation = self.rotation

			diskovery_scene_manager.update_config(self, self.name, 'position')


class HidableEntity(diskovery.RenderedEntity):
	def __init__(self,
		position,
		rotation,
		scale,
		shader_str,
		mesh_str,
		textures_str,
		light_scene="MainLight",
		hidden=False):
		diskovery.RenderedEntity.__init__(self,
			position=position,
			rotation=rotation,
			scale=scale,
			shader_str=shader_str,
			mesh_str=mesh_str,
			light_scene=light_scene,
			textures_str=textures_str)
		self.hidden = hidden

	def update(self, ind):
		diskovery.RenderedEntity.update(self, ind)

	def hide(self):
		if not self.hidden:
			self.hidden = True
			diskovery.refresh()

	def show(self):
		if self.hidden:
			self.hidden = False
			diskovery.refresh()

class Cursor(HidableEntity):
	def __init__(self):
		HidableEntity.__init__(self,
			(0, 0, 0),
			(0, 0, 0),
			(1, 1, 1),
			"Basic",
			"Cursor",
			["Cursor"],
			None,
			True)

	def update(self, ind):
		HidableEntity.update(self, ind)

		if not self.hidden:
			dist = glm.length(self.position - diskovery.camera().position)
			self.scale = glm.vec3(1, 1, 1) * dist/3

		


""" Add any custom Entity extensions here """

class BigBoy(diskovery.RenderedEntity):

	presets = {
			"shader_str": "Default",
			"mesh_str": "Cube",
			"textures_str": ["Cube"]
		}

	def __init__(self, position, rotation, scale):

		diskovery.RenderedEntity.__init__(
			self,
			position=position,
			rotation=rotation,
			scale=scale,
			shader_str=self.presets['shader_str'],
			mesh_str=self.presets['mesh_str'],
			textures_str=self.presets['textures_str']
		)

		self.speed = 0.01

	def update(self, ind):
		diskovery.RenderedEntity.update(self, ind)
		self.position.x += diskovery.input("WalkX") *self.speed
		self.position.z += diskovery.input("WalkY")*self.speed

		if diskovery.input("Spinning"):
			self.rotation.y += self.speed


def barycentric(v1, v2, v3, pos):
		det = (v2.z - v3.z) * (v1.x - v3.x) + (v3.x - v2.x) * (v1.z - v3.z)
		l1 = ((v2.z - v3.z) * (pos.x - v3.x) + (v3.x - v2.x) * (pos.y - v3.z)) / det
		l2 = ((v3.z - v1.z) * (pos.x - v3.x) + (v1.x - v3.x) * (pos.y - v3.z)) / det
		l3 = 1 - l1 - l2
		return l1 * v1.y + l2 * v2.y + l3 * v3.y

def get_height(x, z, terrain):
	unit_size = (2 * terrain.size)/terrain.sub

	dz = x - (terrain.position.x - terrain.size) - unit_size/2
	dx = z - (terrain.position.z - terrain.size) - unit_size/2


	gx = math.floor(dx/(unit_size))
	gz = math.floor(dz/(unit_size))

	if gx < 0 or gz < 0 or gx > len(terrain.heights) - 2 or gz > len(terrain.heights) - 2:
		return terrain.position.y
	else:
		sx = (dx % unit_size) / unit_size
		sz = (dz % unit_size) / unit_size

		if sx <= 1 - sz:
			height = barycentric(glm.vec3(0, terrain.heights[gx][gz], 0),
									  glm.vec3(0, terrain.heights[gx][gz+1], 1),
									  glm.vec3(1, terrain.heights[gx+1][gz], 0),
									  glm.vec2(sx, sz))
		else:
			height = barycentric(glm.vec3(1, terrain.heights[gx+1][gz], 0),
									  glm.vec3(0, terrain.heights[gx][gz+1], 1),
									  glm.vec3(1, terrain.heights[gx+1][gz+1], 1),
									  glm.vec2(sx, sz))

		return height + terrain.position.y

class RunningMan(diskovery.AnimatedEntity):
	
	presets = {
			"shader_str": "Animated",
			"mesh_str": "Man",
			"textures_str": ["Man"],
			"animations_str": ["Run"]
		}

	def __init__(self, position, rotation, scale):

		diskovery.AnimatedEntity.__init__(
			self,
			position=position,
			rotation=rotation,
			scale=scale,
			shader_str=self.presets['shader_str'],
			mesh_str=self.presets['mesh_str'],
			textures_str=self.presets['textures_str'],
			animations_str=self.presets['animations_str'],
			light_scene="Terrain"
		)

		self.speed = 20
		self.running = False

		diskovery.set_camera_target(self)

	

	def update(self, ind):
		diskovery.AnimatedEntity.update(self, ind)
		self.position += self.forward() * -self.speed * diskovery.input("WalkY") * diskovery.frame_time()
		self.position += self.left() * self.speed * diskovery.input("WalkX") * diskovery.frame_time()

		if diskovery.input("WalkX") == 0 and diskovery.input("WalkY") == 0:
			self.running = False
		else:
			self.running = True

		if self.running and not self.animator.playing():
			self.animator.play("Run")
		elif not self.running and self.animator.playing():
			self.animator.stop()

		self.position.y = get_height(self.position.x, self.position.z, diskovery.entity("land"))
		self.rotation.y += diskovery.input("Rotate") * -self.speed * diskovery.frame_time() * 0.05

class Sprite(diskovery.RenderedEntity):

	presets = {
			"shader_str": "GUI",
			"mesh_str": "Default",
			"textures_str": ["Default"]
		}

	def __init__(self, position, rotation, scale):

		diskovery.RenderedEntity.__init__(
			self,
			position=position,
			rotation=rotation,
			scale=scale,
			shader_str=self.presets['shader_str'],
			mesh_str=self.presets['mesh_str'],
			textures_str=self.presets['textures_str']
		)

	def update(self, ind):
		diskovery.RenderedEntity.update(self, ind)
		dim = diskovery.dimensions()
		s = ScreenSize(dim[0], dim[1])
		self.uniforms[1].update(s.get_data(), ind)

class Tree(diskovery.RenderedEntity):

	presets = {
		"shader_str": "Default",
		"mesh_str": "Tree",
		"textures_str": ["Tree"]
	}

	def __init__(self, position, rotation, scale):

		diskovery.RenderedEntity.__init__(
			self,
			position=position,
			rotation=rotation,
			scale=scale,
			shader_str=self.presets['shader_str'],
			mesh_str=self.presets['mesh_str'],
			textures_str=self.presets['textures_str'],
			light_scene="Terrain"
		)
		self.position.y = get_height(self.position.x, self.position.z, diskovery.entity("land")) + 0.3
		
class Rock(diskovery.RenderedEntity):

	presets = {
		"shader_str": "Default",
		"mesh_str": "Rock",
		"textures_str": ["Boulder"]
	}

	def __init__(self, position, rotation, scale):

		diskovery.RenderedEntity.__init__(
			self,
			position=position,
			rotation=rotation,
			scale=scale,
			shader_str=self.presets['shader_str'],
			mesh_str=self.presets['mesh_str'],
			textures_str=self.presets['textures_str'],
			light_scene="Terrain"
		)
		self.position.y = get_height(self.position.x, self.position.z, diskovery.entity("land")) + 0.01

class Plant(diskovery.RenderedEntity):

	presets = {
		"shader_str": "Default",
		"mesh_str": "Plant",
		"textures_str": ["Plant"]
	}

	def __init__(self, position, rotation, scale):

		diskovery.RenderedEntity.__init__(
			self,
			position=position,
			rotation=rotation,
			scale=scale,
			shader_str=self.presets['shader_str'],
			mesh_str=self.presets['mesh_str'],
			textures_str=self.presets['textures_str'],
			light_scene="Terrain"
		)
		self.position.y = get_height(self.position.x, self.position.z, diskovery.entity("land")) + 0.01

class Cube(diskovery.RenderedEntity):

	presets = {
		"shader_str": "Default",
		"mesh_str": "Cube",
		"textures_str": ["Cube"]
	}

	def __init__(self, position, rotation, scale):

		diskovery.RenderedEntity.__init__(
			self,
			position=position,
			rotation=rotation,
			scale=scale,
			shader_str=self.presets['shader_str'],
			mesh_str=self.presets['mesh_str'],
			textures_str=self.presets['textures_str']
		)
