# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
dirname = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, dirname)

try:
	from endplay.config import __version__
	print(f"Using system version of endplay (version {__version__})")
except ImportError:
	root_dir = os.path.join(dirname, "..", "..")
	sys.path.insert(0, root_dir)
	try:
		from endplay.config import __version__
		print(f"No system installation of endplay found, using in-source build of endplay (version {__version__})")
	except ImportError:
		print("Could not import endplay from system or from the root directory; you need to either install " + 
			"a version to your site-packages directory or perform an in-source build by setting " + 
			"CMAKE_INSTALL_PREFIX to <root_directory>/endplay")


# -- Project information -----------------------------------------------------

project = 'endplay'
copyright = '2021, Dominic Price'
author = 'Dominic Price'

# The full version, including alpha/beta/rc tags
from endplay.config import __version__
release = __version__

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
	'sphinxcontrib.apidoc',
	'sphinx.ext.autodoc',
	'myst_parser',
	'autodoc_rename',
	'parse_readme',
	'autodocsumm'
]

apidoc_module_dir = os.path.join(dirname, "..", "..", "endplay")
apidoc_output_dir = os.path.join(dirname, "build", "reference")
apidoc_excluded_paths = []
apidoc_separate_modules = True
apidoc_module_first = True
apidoc_extra_args = ["-P"]

autodoc_default_options = { 'autosummary': True }

readme_module_dir = os.path.join(dirname, "..", "..")
readme_output_dir = os.path.join(dirname, "build", "readme")

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = [ ]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

html_css_files = [
	'css/split_params.css'
]
