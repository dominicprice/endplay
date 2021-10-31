#!/usr/bin/env python3

from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext as build_ext_orig

class CMakeExtension(Extension):
	def __init__(self, name):
		super().__init__(name, sources=[])

class build_ext(build_ext_orig):
	def run(self):
		for ext in self.extensions:
			self.build_cmake(ext)
		super().run()

	def build_cmake(self):
