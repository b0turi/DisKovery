#version 450
#extension GL_ARB_separate_shader_objects : enable

const int MAX_JOINTS = 50;
const int MAX_WEIGHTS = 3;

layout(binding = 1) uniform MVPMatrix
{
    mat4 model;
    mat4 view;
    mat4 proj;
} mvp;

layout(binding = 3) uniform JointData 
{
	mat4 joints[MAX_JOINTS];
} j;

layout(location = 0) in vec3 inPosition;
layout(location = 1) in vec3 inColor;
layout(location = 2) in vec2 inTexCoord;
layout(location = 3) in vec3 inNormal;
layout(location = 4) in vec3 inJointIndices;
layout(location = 5) in vec3 inWeights;

layout(location = 0) out vec3 fragColor;
layout(location = 1) out vec2 fragTexCoord;
layout(location = 2) out vec3 fragNormal;
layout(location = 3) out vec4 worldPosition;

void main()
{

	vec4 totalLocalPos = vec4(0.0);
	vec4 totalNormal = vec4(0.0);

	for (int i = 0; i < MAX_WEIGHTS; i++)
	{
		mat4 transform = j.joints[int(inJointIndices[i])];
		vec4 position = transform * vec4(inPosition, 1.0);
		totalLocalPos += position * inWeights[i];

		vec4 worldNormal = transform * vec4(inNormal, 0.0);
		totalNormal += worldNormal * inWeights[i];
	}


	worldPosition = mvp.model * totalLocalPos;
    gl_Position = mvp.proj * mvp.view * worldPosition;
    fragColor = inColor;
    fragTexCoord = inTexCoord;
    fragNormal = (mvp.model * totalNormal).xyz;
}
