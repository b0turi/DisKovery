#!/bin/env python

import pygame
from sdl2 import *
from sdl2.ext import *
from vulkan import *
from diskovery_vulkan import get_vulkan_command

import ctypes

extensions = ['VK_KHR_surface', 'VK_EXT_debug_report']
layers = ['VK_LAYER_LUNARG_standard_validation']

# Methods for creating surfaces on Windows, Mac OS, and Linux

def surface_xlib(wm_info, instance):
    surface_create = VkXlibSurfaceCreateInfoKHR(
        sType=VK_STRUCTURE_TYPE_XLIB_SURFACE_CREATE_INFO_KHR,
        dpy=wm_info.info.x11.display,
        window=wm_info.info.x11.window,
        flags=0)
    return get_vulkan_command(instance, "vkCreateXlibSurfaceKHR")(instance, surface_create, None)

def surface_wayland(wm_info, instance):
    surface_create = VkWaylandSurfaceCreateInfoKHR(
        sType=VK_STRUCTURE_TYPE_WAYLAND_SURFACE_CREATE_INFO_KHR,
        display=wm_info.info.wl.display,
        surface=wm_info.info.wl.surface,
        flags=0)
    return get_vulkan_command(instance, "vkCreateWaylandSurfaceKHR")(instance, surface_create, None)

def surface_win32(wm_info, instance):
    def get_instance(hWnd):
        from cffi import FFI
        _ffi = FFI()
        _ffi.cdef('long __stdcall GetWindowLongA(void* hWnd, int nIndex);')
        _lib = _ffi.dlopen('User32.dll')
        return _lib.GetWindowLongA(_ffi.cast('void*', hWnd), -6)

    surface_create = VkWin32SurfaceCreateInfoKHR(
        sType=VK_STRUCTURE_TYPE_WIN32_SURFACE_CREATE_INFO_KHR,
        hinstance=get_instance(wm_info.info.win.window),
        hwnd=wm_info.info.win.window,
        flags=0)
    return get_vulkan_command(instance, "vkCreateWin32SurfaceKHR")(instance, surface_create, None)


class DiskoveryWindow:
	def __init__(self, width, height):
		self.window = None
		self.instance = None
		self.surface = None

		self.make_window(width, height)
		self.make_instance()
		self.link_surface()

	def make_window(self, width, height):
		self.window = SDL_CreateWindow(
			"Diskovery".encode('ascii'),
			SDL_WINDOWPOS_UNDEFINED,
			SDL_WINDOWPOS_UNDEFINED, width, height, 0)

		if not self.window:
			raise Exception(SDL_GetError())

		self.wm_info = SDL_SysWMinfo()
		SDL_VERSION(self.wm_info.version)
		SDL_GetWindowWMInfo(self.window, ctypes.byref(self.wm_info))

	def make_instance(self):

		appInfo = VkApplicationInfo(
			sType=VK_STRUCTURE_TYPE_APPLICATION_INFO,
			pApplicationName="Hello World",
			applicationVersion=VK_MAKE_VERSION(1, 0, 0),
			pEngineName="DisKovery",
			engineVersion=VK_MAKE_VERSION(0, 0, 1),
			apiVersion=VK_API_VERSION_1_0)

		# Add platform specific extensions for displaying a window
		
		if self.wm_info.subsystem == SDL_SYSWM_WINDOWS: # Windows
			extensions.append('VK_KHR_win32_surface')
		elif self.wm_info.subsystem == SDL_SYSWM_X11: # Mac OS
			extensions.append('VK_KHR_xlib_surface')
		elif self.wm_info.subsystem == SDL_SYSWM_WAYLAND: # Linux
			extensions.append('VK_KHR_wayland_surface')
		else:
			raise Exception("This platform is not supported!")

		createInfo = VkInstanceCreateInfo(
			sType=VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO,
			flags=0,
			pApplicationInfo=appInfo,
			enabledExtensionCount=len(extensions),
			ppEnabledExtensionNames=extensions,
			enabledLayerCount=len(layers),
			ppEnabledLayerNames=layers)

		self.instance = vkCreateInstance(createInfo, None)

	def link_surface(self):
		surface_mapping = {
		    SDL_SYSWM_X11: surface_xlib,
		    SDL_SYSWM_WAYLAND: surface_wayland,
		    SDL_SYSWM_WINDOWS: surface_win32
		}

		self.surface = surface_mapping[self.wm_info.subsystem](self.wm_info, self.instance)

	def cleanup(self):
		get_vulkan_command(self.instance, "vkDestroySurfaceKHR")(self.instance, self.surface, None)
		vkDestroyInstance(self.instance, None)
		SDL_DestroyWindow(self.window)
		SDL_Quit()