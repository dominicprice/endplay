#!/usr/bin/env python3

import os
import pathlib
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext

class CMakeExtension(Extension):
	"""
	Stub class to distinguish between default extensions and CMake
	extensions (which contain no sources as these are listed in the
	CMakeLists.txt file)
	"""
	def __init__(self, name):
		# don't invoke the original build_ext for this special extension
		super().__init__(name, sources=[])

class cmakeable_build_ext(build_ext):
	"""
	build_ext compatible class which detects if the extension it is to
	build is a CMakeExtension in which case it delegates building to
	the CMake executable.
	"""
	def run(self):
		for ext in self.extensions:
			if isinstance(ext, CMakeExtension):
				self.build_cmake(ext)
		super().run()

	def build_cmake(self, ext):
		cwd = pathlib.Path().absolute()

		# Create directory structure
		build_temp = pathlib.Path(self.build_temp)
		build_temp.mkdir(parents=True, exist_ok=True)
		extdir = pathlib.Path(self.get_ext_fullpath(ext.name))
		extdir.mkdir(parents=True, exist_ok=True)

		# Check which architecture we should be building for
		import struct
		bits = struct.calcsize('P') * 8

		# Setup args passed to cmake
		config = 'Debug' if self.debug else 'Release'
		cmake_config_args = [
			'-DCMAKE_INSTALL_PREFIX=' + str(extdir.parent.absolute()),
			'-DCMAKE_BUILD_TYPE=' + config,
			'-DSETUPTOOLS_BUILD=1'
		]
		if os.name == 'nt':
			if bits == 64: cmake_config_args.append('-A x64')
			elif bits == 32: cmake_config_args.append('-A Win32')
			else: raise RuntimeError(f"Unknown computer architecture with {bits} bits")
		else:
			if bits == 32: cmake_config_args.append('-DCOMPILE_32_BITS=1')

		cmake_build_args = [
			"--build", ".",
			"--target", "install",
			"--config", config
		]

		# Disable warning MSB8029 (https://stackoverflow.com/a/60301902/5194459)
		os.environ["IgnoreWarnIntDirInTempDetected"] = "true"

		os.chdir(str(build_temp))
		self.spawn(['cmake', str(cwd)] + cmake_config_args)
		if not self.dry_run:
			self.spawn(['cmake'] + cmake_build_args)
		os.chdir(str(cwd))

setup(
	ext_modules = [CMakeExtension('endplay')],
	cmdclass = {
		'build_ext': cmakeable_build_ext,
	},
	test_suite = "tests"
)