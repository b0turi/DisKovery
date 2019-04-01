#version 450
#extension GL_ARB_separate_shader_objects : enable

const int MAX_LIGHTS = 1;

layout(binding = 1) uniform sampler2D tex;

vec3 lightPos = vec3(0, 0, 0);
vec3 lightDirection = vec3(0, 0, 0);
vec3 lightTint = vec3(1, 0.8, 0.8);


float ambient = 0.3;
float lightIntensity = 1;
float lightDistance = 5;


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

		if(lightDirection != vec3(0.0))
		{
			// Directional Light
			lightVector = lightDirection;
		}else{
			// Point Light
			lightVector = lightPos - worldPosition.xyz;
			proximity = clamp(length(lightVector)/lightDistance, 0, 1);
		}

		float nDotl = dot(unitNormal, normalize(lightVector));
		float brightness = ((1 - ambient) * max(nDotl, 0.0) * (1-proximity) * lightIntensity) + ambient;

		vec3 diffuse = brightness * lightTint;

		totalLightingColor += vec4(diffuse, 1.0);
	}
	
    outColor = totalLightingColor * texture(tex, fragTexCoord);
}