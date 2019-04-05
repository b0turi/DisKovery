
import diskovery
import diskovery_scene_manager

def main():
	diskovery.init(False, {'input': "editorinput.in"})

	diskovery_scene_manager.edit_scene("template.dk")

	diskovery.run()

if __name__ == '__main__':
	main()
