import pygame

class Sound:
	def __init__(self, filename, loop, volume):
		self.filename = filename
		self.loop = loop
		self.volume = volume

		if not self.loop:
			self.sound = pygame.mixer.Sound(self.filename)
			self.sound.set_volume(self.volume)

	def play(self):
		if self.loop:
			pygame.mixer.music.load(self.filename)
			pygame.mixer.music.set_volume(self.volume)

			pygame.mixer.music.play(loops=-1)

		else:
			self.sound.play()

	def pause(self):
		if self.loop:
			pygame.mixer.music.pause()
		else:
			self.sound.pause()

	def resume(self):
		if self.loop:
			pygame.mixer.music.unpause()
		else:
			self.sound.unpause()
