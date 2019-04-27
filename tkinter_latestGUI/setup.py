from distutils.core import setup
import sys

sys.path.append("C:\\Users\\olive\\anaconda3\\lib\\site-packages\\")

import py2exe

setup(
	console=['hello.py']
	)