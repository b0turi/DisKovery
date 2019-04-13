#version 450
#extension GL_ARB_separate_shader_objects : enable

layout(binding = 1) uniform MVPMatrix {
    mat4 model;
    mat4 view;
    mat4 proj;
} mvp;

layout(location = 0) in vec3 inPosition;
layout(location = 1) in vec3 inColor;
layout(location = 2) in vec2 inTexCoord;
layout(location = 3) in vec3 inNormal;

layout(location = 0) out vec2 fragTexCoord;

void main() {
    gl_Position = mvp.proj * mvp.view * mvp.model * vec4(inPosition, 1.0);
    fragTexCoord = inTexCoord;
}