# -*- coding: utf-8 -*-
"""
Created on Mon Feb 11 15:49:35 2019

@author: olive
"""
import tkinter as tk
#from PIL import Image, ImageTk

f_width = 1280 #default width
f_height = 720 #default height

root = tk.Tk()
# Methods
def hello():
    print ("hello!")

#image = Image.open("Xenoblade-Chronicles-2.gif")
#photo = ImageTk.PhotoImage(image)
#logo = tk.PhotoImage(file ="Xenoblade-Chronicles-2.gif")

w1 = tk.Frame(root) # image = photo
#w1.photo = photo
w1.pack()

def subwin():
   w2 = tk.Listbox(root, width = f_width, height = f_height)
   w2.insert(1, "Python")
   w2.insert(2, "PHP")
   w2.pack()
   while(True):
       root.update()

#create a top level menu
menubar = tk.Menu(root)
menubar.add_command(label="File", command=hello())
menubar.add_command(label="Edit", command=subwin())
menubar.add_command(label="Exit", command=root.destroy)

root.config(menu = menubar) # Hello
while (True):
    root.update()


"""
end
"""
