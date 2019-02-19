#!/bin/env python

import diskovery

def main():
	diskovery.init()

	diskovery.add_mesh("test.obj")

	diskovery.run()

if __name__ == "__main__":
	main()