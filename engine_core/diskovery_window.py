import pygame, platform, vk
from ctypes import byref

def surface_xlib(wm_info, dk):
    surface_create = vk.XlibSurfaceCreateInfoKHR(
        s_type=vk.STRUCTURE_TYPE_XLIB_SURFACE_CREATE_INFO_KHR,
        dpy=wm_info['display'],
        window=wm_info['window'],
        flags=0
    )

    surface = vk.SurfaceKHR(0)
    result = dk.CreateXlibSurfaceKHR(dk.instance, byref(surface_create), None, byref(surface))
    if result == vk.SUCCESS:
    	return surface
    else:
    	raise RuntimeError("Unable to create XLib surface")

def surface_wayland(wm_info, dk):
    surface_create = vk.WaylandSurfaceCreateInfoKHR(
        s_type=vk.STRUCTURE_TYPE_WAYLAND_SURFACE_CREATE_INFO_KHR,
        display=wm_info['display'],
        surface=wm_info['window'],
        flags=0
    )

    surface = vk.SurfaceKHR(0)
    result = dk.CreateWaylandSurfaceKHR(dk.instance, byref(surface_create), None, byref(surface))
    if result == vk.SUCCESS:
    	return surface
    else:
    	raise RuntimeError("Unable to create Wayland surface")

def surface_win32(wm_info, dk):
    def get_instance(hWnd):
        from cffi import FFI
        _ffi = FFI()
        _ffi.cdef('long __stdcall GetWindowLongA(void* hWnd, int nIndex);')
        _lib = _ffi.dlopen('User32.dll')
        return _lib.GetWindowLongA(_ffi.cast('void*', hWnd), -6)

    surface_create = vk.Win32SurfaceCreateInfoKHR(
        s_type=vk.STRUCTURE_TYPE_WIN32_SURFACE_CREATE_INFO_KHR,
        hinstance=get_instance(wm_info['window']),
        hwnd=wm_info['window'],
        flags=0
    )

    surface = vk.SurfaceKHR(0)
    result = dk.CreateWin32SurfaceKHR(dk.instance, byref(surface_create), None, byref(surface))
    if result == vk.SUCCESS:
    	return surface
    else:
    	raise RuntimeError("Unable to create Win32 surface")

class Window:
	def __init__(self, dk, config):
		self.dk = dk

		pygame.display.init()

		self.width = config.get('width') if config.get('width') else 1280
		self.height = config.get('height') if config.get('height') else 720

		full = config.get('fullscreen') if config.get('fullscreen') else False
		# A window can't be resizable if it's fullscreen
		resi = config.get('resizable') if config.get('resizable') and not full else False

		flags = (pygame.FULLSCREEN if full else 0) | (pygame.RESIZABLE if resi else 0)
		pygame.display.set_mode((self.width, self.height), flags)

		self.wm_info = pygame.display.get_wm_info()

		surface_map = {
			'Linux': surface_xlib,
			'Darwin': surface_wayland,
			'Windows': surface_win32
		}

		self.surface = surface_map[platform.system()](self.wm_info, dk)

	def size(self):
		return (self.width, self.height)

	def cleanup(self):
		self.dk.DestroySurfaceKHR(self.dk.instance, self.surface, None)
		pygame.display.quit()


