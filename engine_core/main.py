import diskovery
from diskovery_descriptor import BindingType, UniformType

diskovery.init(True)

diskovery.add_mesh("test.obj", "Default")
diskovery.add_texture("test.png", "Default")
diskovery.add_shader(
	"Default",
	["default.vert", "default.frag"],
	( BindingType.UNIFORM_BUFFER, ),
	[ UniformType.MVP_MATRIX ]
)

re = diskovery.RenderedEntity(
	shade="Default",
	textures="Default",
	mesh="Default"
)


re.cleanup()
diskovery.run()