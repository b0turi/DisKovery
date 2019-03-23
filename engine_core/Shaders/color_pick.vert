#version 450
#extension GL_ARB_separate_shader_objects : enable

layout(binding = 0) uniform UniformBufferObject {
    mat4 model;
    mat4 view;
    mat4 proj;
} ubo;

layout(binding = 1) uniform ObjectColor 
{
	vec3 color;
} c;

layout(binding = 2) uniform ScreenSize
{
	float width;
	float height;
} s;

layout(binding = 3) uniform IsGUI 
{ 
	float is_gui; 
} g;

layout(location = 0) in vec3 inPosition;
layout(location = 1) in vec3 inColor;
layout(location = 2) in vec2 inTexCoord;
layout(location = 3) in vec3 inNormal;

layout(location = 0) out vec3 fragColor;

void main() {
	if(g.is_gui > 0.5)
	{
		mat4 newTransform = mat4(ubo.model);
	
		newTransform[3][0] *= (1/s.width);
		newTransform[3][0] *= 2;
		newTransform[3][0] -= 1;
		
		newTransform[3][1] *= (1/s.height);
		newTransform[3][1] *= 2;
		newTransform[3][1] -= 1;

		gl_Position = newTransform * vec4(inPosition.x/s.width * 2, inPosition.y/s.height * 2, inPosition.z, 1.0);
    }
	else
	{
	    gl_Position = ubo.proj * ubo.view * ubo.model * vec4(inPosition, 1.0);
	}
	fragColor = c.color;
}