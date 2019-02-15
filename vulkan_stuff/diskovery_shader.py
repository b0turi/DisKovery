import os
import subprocess

class Shader:
	def __init__(self, sources, definition, uniforms):

		self.filenames = []

		# Compile GLSL shaders to spir-v files
		os.chdir("shaders")
		for source in sources:
			name = source.split('.')[0]
			subprocess.call("glslangValidator.exe -V {} -o {}.spv".format(source, name))
			self.filenames.append("shaders/{}.spv".format(name))

		self.definition = definition
		self.uniforms = uniforms