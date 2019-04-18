#version 450
#extension GL_ARB_separate_shader_objects : enable

const int MAX_LIGHTS = 50;

layout(binding = 0) uniform sampler2D tex;

layout(binding = 2) uniform SceneLighting
{
		vec4 position[MAX_LIGHTS];
		vec4 direction[MAX_LIGHTS];
		vec4 tint[MAX_LIGHTS];

		// Modifiers held in a vec4 for consistency
		// x - intensity
		// y - distance
		// z - spread
		vec4 modifiers[MAX_LIGHTS];
} lights;

float ambient = 0.3;

layout(location = 0) in vec3 fragColor;
layout(location = 1) in vec2 fragTexCoord;
layout(location = 2) in vec3 fragNormal;
layout(location = 3) in vec4 worldPosition;

layout(location = 0) out vec4 outColor;

void main() {

	if (texture(tex, fragTexCoord).a < 0.5)
		discard;

	vec4 totalLightingColor = vec4(0.0);
	vec3 unitNormal = normalize(fragNormal);

	for(int i = 0; i < MAX_LIGHTS; i++)
	{
		if(lights.position[i] == vec4(0.0) && 
			lights.direction[i] == vec4(0.0) && 
			lights.tint[i] == vec4(0.0) &&
			lights.modifiers[i] == vec4(0.0))
		{
			break;
		}else{
			vec3 lightVector = vec3(0.0);
			float proximity = 0.0;

			if(lights.direction[i] != vec4(0.0))
			{
				// Directional Light
				lightVector = lights.direction[i].xyz;
			}else{
				// Point Light
				lightVector = lights.position[i].xyz - worldPosition.xyz;

				if(lights.modifiers[i].y == 0)
					proximity = clamp(length(lightVector)/lights.modifiers[i].y, 0, 1);
				else
					proximity = 0;
			}

			float nDotl = dot(unitNormal, normalize(lightVector));
			float brightness = ((1 - ambient) * max(nDotl, 0.0) * (1-proximity) * lights.modifiers[i].x) + ambient;

			vec3 diffuse = brightness * lights.tint[i].xyz;

			totalLightingColor += vec4(diffuse, 1.0);
		}
		
	}

	
    outColor = totalLightingColor * texture(tex, fragTexCoord);
}
