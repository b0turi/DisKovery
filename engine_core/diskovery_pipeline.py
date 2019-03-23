#!/bin/env/python

import vk
import os
import subprocess
from ctypes import *
from diskovery_mesh import Vertex, bindings, attributes, animated_attributes

class Shader(object):
	def __init__(self, sources, definition, uniforms):
		# A tuple defining the order of the descriptor sets as uniforms and samplers
		self.definition = definition
		# A breakdown of what each of the above uniforms contains
		self.uniforms = uniforms
		# A dictionary of the filenames of each stage of the shader
		self.filenames = {}

		"""
		Shaders are typically written in a C-style language called GLSL.
		Vulkan does not interpret GLSL shaders, but instead a new, binary
		format called SPIR-V. Thankfully, included in the Vulkan SDK is an
		executable that allows GLSL shaders to be converted into SPIR-V format.

		The following searches the directory where the shaders are located and
		formats the newly created SPIR-V shaders into a dictionary where they
		can be referenced by calling their stage in the shader.

		This functionality requires that the GLSL shaders use file endings that
		correspond to their stages (e.g. *.vert, *.frag)
		"""
		os.chdir("Shaders")

		for src in sources:
			# if os.path.isfile("{}.spv".format(src)):
			# 	subprocess.call("rm {}.spv".format(src))
			# subprocess.call("glslangValidator.exe -V {} -o {}.spv".format(src, src))
			# subprocess.call("compile.bat {}".format(src))
			self.filenames[src.split('.')[1]] = "shaders/{}.spv".format(src)

		os.chdir("..")

class Pipeline(object):

	def make_pipeline_layout(self, set_layout):
		create_info = vk.PipelineLayoutCreateInfo(
			s_type=vk.STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO,
			flags=0,
			set_layout_count=1,
			set_layouts=pointer(set_layout),
			push_constant_range_count=0
		)

		self.dk.CreatePipelineLayout(
			self.dk.device,
			byref(create_info),
			None,
			byref(self.pipeline_layout)
		)

	def get_shader_module(self, src):
		src_size = len(src)
		src = (c_ubyte*src_size)(*src)

		module_create = vk.ShaderModuleCreateInfo(
			s_type=vk.STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO,
			flags=0,
			code_size=src_size,
			code=cast(src, POINTER(c_uint))
		)

		module = vk.ShaderModule(0)
		self.dk.CreateShaderModule(
			self.dk.device,
			byref(module_create),
			None,
			byref(module)
		)
		return module

	def make_pipeline(self, animated, samples):
		path = os.path.dirname(os.path.abspath(__file__))
		with open(os.path.join(path, self.shader.filenames['vert']), 'rb') as f:
			vert_shader_src = f.read()
		with open(os.path.join(path, self.shader.filenames['frag']), 'rb') as f:
			frag_shader_src = f.read()

		vertex_shader = self.get_shader_module(vert_shader_src)
		fragment_shader = self.get_shader_module(frag_shader_src)

		vertex_stage_create = vk.PipelineShaderStageCreateInfo(
			s_type=vk.STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO,
			stage=vk.SHADER_STAGE_VERTEX_BIT,
			module=vertex_shader,
			name=b'main'
		)

		fragment_stage_create = vk.PipelineShaderStageCreateInfo(
			s_type=vk.STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO,
			stage=vk.SHADER_STAGE_FRAGMENT_BIT,
			module=fragment_shader,
			name=b'main'
		)

		vertex_input_create = vk.PipelineVertexInputStateCreateInfo(
		    s_type=vk.STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO,
		    vertex_binding_description_count=1,
		    vertex_attribute_description_count=len(attributes()),
		    vertex_binding_descriptions=cast(
		    	bindings(),
		    	POINTER(vk.VertexInputBindingDescription)
		    ),
		    vertex_attribute_descriptions=cast(
		    	attributes(),
		    	POINTER(vk.VertexInputAttributeDescription)
		    )
		)

		if animated:
			vertex_input_create.vertex_attribute_description_count = len(animated_attributes())
			vertex_input_create.vertex_attribute_descriptions=cast(
				animated_attributes(),
				POINTER(vk.VertexInputAttributeDescription)
			)

		input_assembly_create = vk.PipelineInputAssemblyStateCreateInfo(
		    s_type=vk.STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO,
		    topology=vk.PRIMITIVE_TOPOLOGY_TRIANGLE_LIST,
		    primitive_restart_enable=vk.FALSE
		)

		viewport = vk.Viewport(
		    width=float(self.dk.image_data['extent'].width),
		    height=float(self.dk.image_data['extent'].height),
		    min_depth=0.,
		    max_depth=1.
		)

		scissor_offset = vk.Offset2D(x=0, y=0)
		scissor = vk.Rect2D(offset=scissor_offset, extent=self.dk.image_data['extent'])
		viewport_state_create = vk.PipelineViewportStateCreateInfo(
		    s_type=vk.STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO,
		    viewport_count=1,
		    viewports=pointer(viewport),
		    scissor_count=1,
		    scissors=pointer(scissor)
		)

		rasterizer_create = vk.PipelineRasterizationStateCreateInfo(
		    s_type=vk.STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO,
		    depth_clamp_enable=vk.FALSE,
		    rasterizer_discard_enable=vk.FALSE,
		    polygon_mode=vk.POLYGON_MODE_FILL,
		    line_width=1,
		    cull_mode=vk.CULL_MODE_BACK_BIT,
		    front_face=vk.FRONT_FACE_CLOCKWISE
		)

		multisample_create = vk.PipelineMultisampleStateCreateInfo(
		    s_type=vk.STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO,
		    sample_shading_enable=vk.FALSE,
		    rasterization_samples=self.dk.image_data['msaa_samples'],
		    min_sample_shading=1
		)

		depth_stencil_create = vk.PipelineDepthStencilStateCreateInfo(
			s_type=vk.STRUCTURE_TYPE_PIPELINE_DEPTH_STENCIL_STATE_CREATE_INFO,
			depth_test_enable=vk.TRUE,
			depth_write_enable=vk.TRUE,
			depth_compare_op=vk.COMPARE_OP_LESS,
			depth_bounds_test_enable=vk.FALSE,
			stencil_test_enable=vk.FALSE
		)

		color_blend_attachment = vk.PipelineColorBlendAttachmentState(
		    color_write_mask=vk.COLOR_COMPONENT_R_BIT |
						    vk.COLOR_COMPONENT_G_BIT |
						    vk.COLOR_COMPONENT_B_BIT |
						    vk.COLOR_COMPONENT_A_BIT,
		    blend_enable=vk.FALSE
		)

		color_blend_create = vk.PipelineColorBlendStateCreateInfo(
		    s_type=vk.STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO,
		    logic_op_enable=vk.FALSE,
		    logic_op=vk.LOGIC_OP_COPY,
		    attachment_count=1,
		    attachments=pointer(color_blend_attachment),
		    blend_constants=(c_float*4)(0.,0.,0.,0.)
		)

		shader_stages = (vk.PipelineShaderStageCreateInfo*2)(vertex_stage_create, fragment_stage_create)

		pipeline_create = vk.GraphicsPipelineCreateInfo(
		    s_type=vk.STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO,
		    stage_count=2,
		    stages=cast(shader_stages, POINTER(vk.PipelineShaderStageCreateInfo)),
		    vertex_input_state=pointer(vertex_input_create),
		    input_assembly_state=pointer(input_assembly_create),
		    viewport_state=pointer(viewport_state_create),
		    rasterization_state=pointer(rasterizer_create),
		    multisample_state=pointer(multisample_create),
		    depth_stencil_state=pointer(depth_stencil_create),
		    color_blend_state=pointer(color_blend_create),
		    dynamic_state=None,
		    layout=self.pipeline_layout,
		    render_pass=self.dk.get_render_pass(samples)
		)

		pipeline = vk.Pipeline(0)
		result = self.dk.CreateGraphicsPipelines(
			self.dk.device,
			vk.PipelineCache(0),
			1,
			byref(pipeline_create),
			None,
			byref(pipeline)
		)

		self.pipeline_ref = pipeline

		self.dk.DestroyShaderModule(self.dk.device, vertex_shader, None)
		self.dk.DestroyShaderModule(self.dk.device, fragment_shader, None)


	def __init__(self, dk, shader, set_layout, animated, samples=None):
		self.dk = dk

		if samples == None:
			samples = self.dk.image_data['msaa_samples']
		self.samples = samples
		# A reference to the Shader (Shader) this pipeline is being built around
		self.shader = shader
		# A restructuring of the definition of the above shader for
		# compatibility with Vulkan's Descriptor sets (VkPipelineLayout)
		self.pipeline_layout = vk.PipelineLayout(0)
		# A reference to the Vulkan pipeline (VkPipeline) itself
		self.pipeline_ref = vk.Pipeline(0)

		self.make_pipeline_layout(set_layout)
		self.make_pipeline(animated, samples)

	def cleanup(self):
		self.dk.DestroyPipelineLayout(self.dk.device, self.pipeline_layout, None)
		self.dk.DestroyPipeline(self.dk.device, self.pipeline_ref, None)
