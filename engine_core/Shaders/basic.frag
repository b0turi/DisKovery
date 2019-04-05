#version 450
#extension GL_ARB_separate_shader_objects : enable

layout(binding = 0) uniform sampler2D tex;

layout(location = 0) in vec2 fragTexCoord;

layout(location = 0) out vec4 outColor;
layout(location = 1) out vec4 nothing;

void main() {
    outColor = texture(tex, fragTexCoord);
    nothing = vec4(0.0);
}