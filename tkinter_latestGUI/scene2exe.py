"""
The :mod:`diskovery` module is the primary module that acts as a wrapper
around the functionality of the other DisKovery submodules. It stores
dictionaries that handle the memory management of assets and objects
to be used in the scene, including:

- :class:`~diskovery_mesh.Mesh` objects for 3D models
- :class:`~diskovery_image.Texture` objects for external images
- :class:`~diskovery_pipeline.Shader` objects for GLSL shader programs
- :class:`~diskovery_pipeline.Pipeline` objects (associated with :class:`~diskovery_pipeline.Shader` objects)
- VkDescriptorSetLayout_ objects (associated with :class:`~diskovery_pipeline.Shader` objects)
- VkSampler_ objects (for sampling :class:`~diskovery_image.Texture` objects)

"""

from distutils.core import setup
import py2exe

setup(console=[