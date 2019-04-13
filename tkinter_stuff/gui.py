
# -*- coding: utf-8 -*-
""" """
import tkinter as tk
import diskov_win as dw
import diskov_menu as mb
screen_wd = 1280
screen_ht = 720
def main():
        root = tk.Tk()
        diskov_app = dw.Display(root, 768, 700, int(screen_wd * 0.2) + 5, 40)
        diskov_opt = mb.Menu_Toolbar(root, 768, 40, int(screen_wd * 0.2) + 5, -20)
        
        while True:
                root.update_idletasks()
                root.update()
main()        
"""
end
"""