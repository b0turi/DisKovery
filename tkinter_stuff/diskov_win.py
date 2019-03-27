#import statements
import tkinter as tk

class diskov_win:

	def __init__(self, width, height, x, y):
		self.root = tk.Tk()
		
		self.width = width
		self.height = height
		self.x = x
		self.y = y
		self.dim = "{0}{1}{2}{3}{4}{5}{6}".format(str(width),'x',str(height),'+',str(x),'+',str(y))
		self.root.geometry(self.dim)
		
		self.root.title('DisKovery Engine v0.01')
		while True:
			self.root.update()