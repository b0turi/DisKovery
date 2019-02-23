from vulkan import *
import os
import diskovery
from sys import getsizeof
from diskovery_mesh import Vertex

def get_shader_module(src):
	module_create = VkShaderModuleCreateInfo(
		sType=VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO,
		flags=0,
		codeSize=len(src),
		pCode=src
	)

	module = vkCreateShaderModule(diskovery.device(), module_create, None)
	return module

class Pipeline:
	def __init__(self, shader, set_layout):

		self.shader = shader
		self.pipeline_layout = None
		self.pipeline_ref = None

		self.make_pipeline_layout(set_layout)
		self.make_pipeline(shader, set_layout)

	def make_pipeline_layout(self, set_layout):
		pipeline_layout_create = VkPipelineLayoutCreateInfo(
		    sType=VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO,
		    flags=0,
		    setLayoutCount=1,
		    pSetLayouts=[set_layout]
		)

		self.pipeline_layout = vkCreatePipelineLayout(
			diskovery.device(), 
			pipeline_layout_create, None
		)

	def make_pipeline(self, shader, set_layout):
		path = os.path.dirname(os.path.abspath(__file__))
		with open(os.path.join(path, shader.filenames['vert']), 'rb') as f:
			vert_shader_src = f.read()
		with open(os.path.join(path, shader.filenames['frag']), 'rb') as f:
			frag_shader_src = f.read()

		vertex_shader = get_shader_module(vert_shader_src)
		fragment_shader = get_shader_module(frag_shader_src)

		vertex_stage_create = VkPipelineShaderStageCreateInfo(
			sType=VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO,
			stage=VK_SHADER_STAGE_VERTEX_BIT,
			module=vertex_shader,
			flags=0,
			pSpecializationInfo=None,
			pName='main'
		)

		fragment_stage_create = VkPipelineShaderStageCreateInfo(
			sType=VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO,
			stage=VK_SHADER_STAGE_FRAGMENT_BIT,
			module=fragment_shader,
			flags=0,
			pSpecializationInfo=None,
			pName='main'
		)

		vertex_input_create = VkPipelineVertexInputStateCreateInfo(
		    sType=VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO,
		    vertexBindingDescriptionCount=1,
		    vertexAttributeDescriptionCount=len(Vertex.attributes()),
		    pVertexBindingDescriptions=Vertex.bindings(),
		    pVertexAttributeDescriptions=Vertex.attributes()
		)

		input_assembly_create = VkPipelineInputAssemblyStateCreateInfo(
		    sType=VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO,
		    flags=0,
		    topology=VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST,
		    primitiveRestartEnable=VK_FALSE
		)

		viewport = VkViewport(
		    x=0., y=0., width=float(diskovery.extent().width), height=float(diskovery.extent().height),
		    minDepth=0., maxDepth=1.
		)

		scissor_offset = VkOffset2D(x=0, y=0)
		scissor = VkRect2D(offset=scissor_offset, extent=diskovery.extent())
		viewport_state_create = VkPipelineViewportStateCreateInfo(
		    sType=VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO,
		    flags=0,
		    viewportCount=1,
		    pViewports=[viewport],
		    scissorCount=1,
		    pScissors=[scissor]
		)

		rasterizer_create = VkPipelineRasterizationStateCreateInfo(
		    sType=VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO,
		    flags=0,
		    depthClampEnable=VK_FALSE,
		    rasterizerDiscardEnable=VK_FALSE,
		    polygonMode=VK_POLYGON_MODE_FILL,
		    lineWidth=1,
		    cullMode=VK_CULL_MODE_BACK_BIT,
		    frontFace=VK_FRONT_FACE_CLOCKWISE,
		    depthBiasEnable=VK_FALSE,
		    depthBiasConstantFactor=0.,
		    depthBiasClamp=0.,
		    depthBiasSlopeFactor=0.
		)

		multisample_create = VkPipelineMultisampleStateCreateInfo(
		    sType=VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO,
		    flags=0,
		    sampleShadingEnable=VK_FALSE,
		    rasterizationSamples=VK_SAMPLE_COUNT_1_BIT,
		    minSampleShading=1,
		    pSampleMask=None,
		    alphaToCoverageEnable=VK_FALSE,
		    alphaToOneEnable=VK_FALSE)

		depth_stencil_create = VkPipelineDepthStencilStateCreateInfo(
			sType=VK_STRUCTURE_TYPE_PIPELINE_DEPTH_STENCIL_STATE_CREATE_INFO,
			depthTestEnable=VK_TRUE,
			depthWriteEnable=VK_TRUE,
			depthCompareOp=VK_COMPARE_OP_LESS,
			depthBoundsTestEnable=VK_FALSE,
			stencilTestEnable=VK_FALSE
		)

		color_blend_attachement = VkPipelineColorBlendAttachmentState(
		    colorWriteMask=VK_COLOR_COMPONENT_R_BIT | 
						    VK_COLOR_COMPONENT_G_BIT | 
						    VK_COLOR_COMPONENT_B_BIT | 
						    VK_COLOR_COMPONENT_A_BIT,

		    blendEnable=VK_FALSE,
		    srcColorBlendFactor=VK_BLEND_FACTOR_ONE,
		    dstColorBlendFactor=VK_BLEND_FACTOR_ZERO,
		    colorBlendOp=VK_BLEND_OP_ADD,
		    srcAlphaBlendFactor=VK_BLEND_FACTOR_ONE,
		    dstAlphaBlendFactor=VK_BLEND_FACTOR_ZERO,
		    alphaBlendOp=VK_BLEND_OP_ADD
		)

		color_blend_create = VkPipelineColorBlendStateCreateInfo(
		    sType=VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO,
		    flags=0,
		    logicOpEnable=VK_FALSE,
		    logicOp=VK_LOGIC_OP_COPY,
		    attachmentCount=1,
		    pAttachments=[color_blend_attachement],
		    blendConstants=[0, 0, 0, 0]
		)

		pipeline_create = VkGraphicsPipelineCreateInfo(
		    sType=VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO,
		    flags=0,
		    stageCount=2,
		    pStages=[vertex_stage_create, fragment_stage_create],
		    pVertexInputState=vertex_input_create,
		    pInputAssemblyState=input_assembly_create,
		    pTessellationState=None,
		    pViewportState=viewport_state_create,
		    pRasterizationState=rasterizer_create,
		    pMultisampleState=multisample_create,
		    pDepthStencilState=depth_stencil_create,
		    pColorBlendState=color_blend_create,
		    pDynamicState=None,
		    layout=self.pipeline_layout,
		    renderPass=diskovery.render_pass(),
		    subpass=0,
		    basePipelineHandle=None,
		    basePipelineIndex=-1
		)

		self.pipeline_ref = vkCreateGraphicsPipelines(
			diskovery.device(), 
			None, 
			1, 
			[pipeline_create], 
			None
		)

		vkDestroyShaderModule(
			diskovery.device(), 
			fragment_shader, 
			None
		)
		vkDestroyShaderModule(
			diskovery.device(), 
			vertex_shader, 
			None
		)

	def cleanup(self):
		vkDestroyPipeline(
			diskovery.device(), 
			self.pipeline_ref, 
			None
		)

		vkDestroyPipelineLayout(
			diskovery.device(), 
			self.pipeline_layout, 
			None
		)
