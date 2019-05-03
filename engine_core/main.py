
import diskovery
import diskovery_scene_manager

def main():
	diskovery.init(False, {'fullscreen':True})

	diskovery_scene_manager.load_scene("terrain.dk")

	diskovery.run()

if __name__ == '__main__':
	main()
