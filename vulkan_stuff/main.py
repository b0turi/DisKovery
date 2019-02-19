#!/bin/env python

import diskovery
from diskovery_mesh import Mesh

def main():
	diskovery.init()

	m = Mesh("test.obj")

	m.cleanup()
	diskovery.run()

if __name__ == "__main__":
	main()