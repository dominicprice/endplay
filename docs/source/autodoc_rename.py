import shutil
import os

def setup(app):
	app.connect("builder-inited", builder_inited)

def builder_inited(app):
	# Change the first line of the 'modules.rst' to be API Reference
	output_dir = app.config.apidoc_output_dir
	print(f"Modifying file {output_dir}/modules.rst")
	modfile = os.path.join(output_dir, "modules.rst")
	bakfile = os.path.join(output_dir, "modules.rst.backup")
	shutil.copyfile(modfile, bakfile)
	with open(bakfile, 'r') as fb:
		with open(modfile, 'w') as fm:
			for _ in range(2):
				fb.readline() # discarded
			title = "API Documentation"
			fm.write(title + "\n")
			fm.write(("=" * len(title)) + "\n")
			shutil.copyfileobj(fb, fm)