
import diskovery 
import diskovery_scene_manager

def main():
	diskovery.init(True)

	diskovery_scene_manager.load_scene("template.dk")

	diskovery.run()

if __name__ == '__main__':
	main()
