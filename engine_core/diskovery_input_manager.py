import pygame
from enum import Enum

class InputType(Enum):
	Keyboard = 0,
	Mouse = 1,
	Gamepad = 2

_keyboard_state = []
_mouse_state = { }
_gamepad_state = { }

class Input(object):
	def __init__(self, in_src, in_ind, in_type, in_mod, neg = False, bin = True):
		self.src = in_src
		self.index = in_ind
		self.i_type = in_type
		self.mod = in_mod
		self.coeff = 1 if not neg else -1

		if in_type == 'R' or in_type == 'A':
			self.value = 0
		elif in_type == 'B':
			self.value = False

		# Handle repeating input, like scrolling through a menu with arrows
		if self.mod == 'R':
			self.time = None
			self.attacked = False
			self.attack_delay = 8000
			self.repeat_delay = 100

		self.acceptable = True

	def update(self):
		global _keyboard_state, _mouse_state, _gamepad_state
		if self.src == InputType.Keyboard:
			self.check_input(_keyboard_state)
		elif self.src == InputType.Mouse:
			self.check_input(_mouse_state)
		elif self.src == InputType.Gamepad and self.is_button:
			self.check_input(_gamepad_state)

	def check_input(self, input_list):
		if input_list[self.index] != 0 and self.acceptable:
			self.value = input_list[self.index] * self.coeff
			if self.mod != 'S':
				self.acceptable = False
				if self.mod == 'R':
					self.time = pygame.time.get_ticks()

		elif input_list[self.index] != 0 and not self.acceptable:
			self.value = 0
			if self.mod == 'R':
				diff = pygame.time.get_ticks() - self.time
				if not self.attacked and diff > self.attack_delay:
					self.acceptable = True
					self.attacked = True
					self.time += diff
				elif self.attacked and diff > self.repeat_delay:
					self.acceptable = True
					self.time += diff

		elif input_list[self.index] == 0:
			self.value = 0
			self.acceptable = True
			if self.mod == 'R':
				self.attacked = False

class InputManager:
	def __init__(self, filename=None):
		self.inputs = { }
		self.default_inputs = { }
		self.input_values = { }
		self.control_set = "Empty"

		if filename:
			self.load_control_set(filename)

	def update(self):
		global _keyboard_state, _mouse_state, _gamepad_state
		_keyboard_state = pygame.key.get_pressed()

		m_delta = pygame.mouse.get_rel()

		_mouse_state = pygame.mouse.get_pressed()
		_mouse_state += m_delta

		for name, inputs in self.inputs.items():
			input_value = 0
			accepted_inputs = 0

			for input in inputs:
				input.update()
				if input.value != 0:
					input_value += input.value
					accepted_inputs += 1

			if accepted_inputs > 0:
				self.input_values[name] = input_value / accepted_inputs
			else:
				self.input_values[name] = 0

	def load_control_set(self, filename):
		self.inputs.clear()
		self.default_inputs.clear()

		input_defs = []

		with open(filename, 'r') as f:

			# Default Keyboard/Mouse, Custom Keyboard/Mouse
			titles = ['dkm', 'ckm']

			source_map = {'K': InputType.Keyboard,
						  'M': InputType.Mouse,
						  'G': InputType.Gamepad }

			mouse_delta_map = { 'x': len(pygame.mouse.get_pressed()),
								'y': len(pygame.mouse.get_pressed()) + 1}

			self.control_set = f.readline()[:-1]

			line = f.readline()[:-1]
			while line and line != "":
				in_type = line[0]
				in_mod = line[1]
				name = line.split(' ')[1]
				input_defs.append((in_type, in_mod, name))
				self.inputs[name] = []
				self.default_inputs[name] = []
				self.input_values[name] = 0
				line = f.readline()[:-1]

			for i in range(0, len(titles)):
				for j in range(0, len(input_defs)):
					line = f.readline()[:-1]
					destination = None
					if i == 0:
						destination = self.default_inputs[input_defs[j][2]]
					else:
						destination = self.inputs[input_defs[j][2]]
					all_ins = " ".join(line.split(' ')[1:]).split(',') if ',' in line else [line[line.index(' ') + 1:]]
					for input in all_ins:
						split_line = input.split(' ')
						for ind, sub_input in enumerate(split_line):
							in_source = source_map[sub_input[0]]
							if in_source == InputType.Keyboard:
								in_index = int(eval("pygame.{}".format(sub_input)))
							else:
								if not isinstance(sub_input[2:], int):
									in_index = mouse_delta_map[sub_input[2:]]
								else:
									in_index = int(sub_input[2:])

							destination.append(Input(
								in_source,
								in_index,
								input_defs[j][0],
								input_defs[j][1],
								(ind == 0) and len(split_line) > 1
							))
