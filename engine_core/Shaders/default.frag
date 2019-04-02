#version 450
#extension GL_ARB_separate_shader_objects : enable

const int MAX_LIGHTS = 1;

layout(binding = 1) uniform sampler2D tex;

layout(binding = 2) uniform SceneLighting
{
		vec3 position[MAX_LIGHTS];
		vec3 direction[MAX_LIGHTS];
		vec3 tint[MAX_LIGHTS];

		float intensity[MAX_LIGHTS];
		float dist[MAX_LIGHTS];
		float spread[MAX_LIGHTS];
} lights;

float ambient = 0.3;

layout(location = 0) in vec3 fragColor;
layout(location = 1) in vec2 fragTexCoord;
layout(location = 2) in vec3 fragNormal;
layout(location = 3) in vec4 worldPosition;

layout(location = 0) out vec4 outColor;

void main() {

	vec4 totalLightingColor = vec4(0.0);

	for(int i = 0; i < MAX_LIGHTS; i++)
	{
		vec3 unitNormal = normalize(fragNormal);
		vec3 lightVector = vec3(0.0);
		float proximity = 0.0;

		if(lights.direction[i] != vec3(0.0))
		{
			// Directional Light
			lightVector = lights.direction[i];
		}else{
			// Point Light
			lightVector = lights.position[i] - worldPosition.xyz;
			proximity = clamp(length(lightVector)/lights.dist[i], 0, 1);
		}

		float nDotl = dot(unitNormal, normalize(lightVector));
		float brightness = ((1 - ambient) * max(nDotl, 0.0) * (1-proximity) * lights.intensity[i]) + ambient;

		vec3 diffuse = brightness * lights.tint[i];

		totalLightingColor += vec4(diffuse, 1.0);
	}

    outColor = totalLightingColor * texture(tex, fragTexCoord);
}
