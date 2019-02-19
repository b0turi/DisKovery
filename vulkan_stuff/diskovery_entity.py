import glm

class Entity():
	def __init__(self, position=None):
		self.position = position if position != None else glm.vec3()

		self.parent = None
		self.children = []

	def world_position(self):
		p = self.parent
		pos = self.position

		while p != None:
			pos += p.position
			p = p.parent

		return pos

	def detach(self):
		self.parent.children.remove(self)
		self.parent = None

	def set_parent(self, parent):
		if self.parent != None:
			self.detach()

		self.parent = parent
		parent.children.append(self)

class RenderedEntity(Entity):
	def __init__(self, 
		position=None, 
		rotation=None, 
		scale=None, 
		pipeline=None,
		textures=None,
		mesh=None):
		Entity.__init__(self, position)

		self.rotation = rotation if rotation != None else glm.vec3()
		self.scale = scale if scale != None else glm.vec3()

		self.pipeline = pipeline if pipeline != None else "Default"
		self.textures = textures if textures != None else ["Default"]
		self.mesh = mesh if mesh != None else None

	

