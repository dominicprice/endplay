#!/usr/bin/env python3

import os
import pathlib
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext as build_ext_orig

class CMakeExtension(Extension):
	def __init__(self, name):
		# don't invoke the original build_ext for this special extension
		super().__init__(name, sources=[])

class build_ext(build_ext_orig):
	def run(self):
		for ext in self.extensions:
			self.build_cmake(ext)
		super().run()

	def build_cmake(self, ext):
		cwd = pathlib.Path().absolute()

		# Create directory structure
		build_temp = pathlib.Path(self.build_temp)
		build_temp.mkdir(parents=True, exist_ok=True)
		extdir = pathlib.Path(self.get_ext_fullpath(ext.name))
		extdir.mkdir(parents=True, exist_ok=True)

		# Setup args passed to cmake
		config = 'Debug' if self.debug else 'Release'
		cmake_config_args = [
			'-DCMAKE_INSTALL_PREFIX=' + str(extdir.parent.absolute()),
			'-DCMAKE_BUILD_TYPE=' + config
		]
		cmake_build_args = [
			"--build", ".",
			"--target", "install",
			"--config", config
		]

		os.chdir(str(build_temp))
		self.spawn(['cmake', str(cwd)] + cmake_config_args)
		if not self.dry_run:
			self.spawn(['cmake'] + cmake_build_args)
		os.chdir(str(cwd))


with open("README.md", encoding='utf-8') as f:
	long_description = f.read()
with open("VERSION", encoding="utf-8") as f:
	version = f.read().strip()

metadata = {
	"name": "endplay",
	"version": version,
	"author": "Dominic Price",
	"author_email": "dominicprice@outlook.com",
	"description": "A suite of tools for generation and analysis of bridge deals",
	"long_description": long_description,
	"long_description_content_type": "text/markdown",
	"url": "https://gitlab.com/dominicprice/endplay",
	"classifiers": [
		"Development Status :: 4 - Beta",
		"Natural Language :: English",
		"Topic :: Games/Entertainment",
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent"
	],
	"keywords": "bridge,cards,games,double dummy,dds,analysis,stats,deal,dealer",
	"project_urls": {
		"Documentation": "https://endplay.readthedocs.io",
		"Bug Tracker": "https://gitlab.com/dominicprice/endplay/-/issues"
	}
}

packages = [
	"endplay",
	"endplay._dds",
	"endplay.dds",
	"endplay.dealer",
	"endplay.dealer.actions",
	"endplay.evaluate",
	"endplay.interact",
	"endplay.parsers",
	"endplay.types"
]

setup(
	**metadata,
	python_requires = ">=3.9",
	install_requires = [
		"pyparsing",
		"tqdm"
	],
	packages = packages,
	ext_modules=[CMakeExtension('endplay/_dds')],
	cmdclass={
		'build_ext': build_ext,
	},
	test_suite = "tests"
)