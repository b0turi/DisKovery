import pygame
from enum import Enum

class InputType(Enum):
	KEYBOARD = 0,
	MOUSE = 1,
	GAMEPAD = 2

class InputManager:
	def __init__(self):
		self.keyboard_inputs = { }
		self.mouse_inputs = { }
		self.gamepad_inputs = { }

	def add_input(self, name, binding, input_type, analog=False):
		if input_type == InputType.KEYBOARD and analog:
			print("DisKovery WARNING: Analog input mapped to binary device. " \
				  "Precision may be lost.")



	def get_inputs_state(self):
		states = pygame.key.get_pressed()

