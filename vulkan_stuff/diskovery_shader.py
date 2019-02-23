import os
import subprocess

class Shader:
	def __init__(self, sources, definition, uniforms):

		self.filenames = {}

		os.chdir("shaders")

		for source in sources:
			name = source.split('.')[0]
			if not os.path.isfile("{}.spv".format(name)):
				subprocess.call("glslangValidator.exe -V {} -o {}.spv".format(source, name))
			self.filenames[source.split('.')[1]] = "shaders/{}.spv".format(name)

		os.chdir("..")

		self.definition = definition
		self.uniforms = uniforms

	def __str__(self):
		return "Filenames: {}\nDefinition: {}\n Uniforms: {}".format(self.filenames, self.definition, self.uniforms)