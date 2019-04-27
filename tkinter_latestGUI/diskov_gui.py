#!/bin/env/python
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

import tkinter as tk
from tkinter import *
import os
import sys

sys.path.append(os.path.abspath('../engine_core/'))
import diskovery
import diskovery_scene_manager
import pygame


"""
Initializer
"""
mui = tk.Tk()

"""
:function: 'main'
Creates the UI in the Pygame window
"""
def main():
