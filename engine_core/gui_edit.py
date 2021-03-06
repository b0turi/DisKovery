# -*- coding: utf-8 -*-
""" """
import tkinter as tk
import diskov_win_edit as dw
import diskov_menu as dm

import os
import sys

sys.path.append(os.path.abspath('../engine_core/'))
import diskovery
import diskovery_scene_manager
import pygame

root = tk.Tk()
def main():
	diskov_app = dw.Display(root, diskovery.quit)
	diskov_menu = dm.Menu_Toolbar(root, diskov_app)

	root.update()
	os.environ['SDL_WINDOWID'] = str(diskov_app.embed.winfo_id())

	diskovery.init(False, {'input': "editorinput.in"})
	diskovery_scene_manager.edit_scene("terrain.dk", root)
	diskovery.run(root)

main()

"""
end
"""
