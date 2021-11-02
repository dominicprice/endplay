import re
import os
import shutil

def setup(app):
	app.connect('builder-inited', builder_inited)
	app.add_config_value('readme_root_dir', None, 'env', [str])
	
def builder_inited(app):
	# Read the markdown file and create files based on the 
	# section headers
	root_dir = app.config.readme_root_dir
	newsection = re.compile(r"^(#+)\s+(.*)$")
	print("Writing file intro.md")
	curfile = open(os.path.join(root_dir, "source", "intro.md"), 'w', encoding="utf-8")
	with open(os.path.join(root_dir, "..", "..", "README.md"), encoding="utf-8") as f:
		for line in f:
			m = newsection.match(line)
			if m:
				hlevel = len(m[1])
				if hlevel == 1:
					curfile.write("# What is endplay?\n")
				elif hlevel == 2:
					curfile.close()
					name = m[2].replace(" ", "_").lower()
					print("Writing file", name + ".md")
					curfile = open(os.path.join(root_dir, "source", name + ".md"), 'w', encoding="utf-8")
					curfile.write("# " + m[2] + "\n")
				else:
					new_h = "#" * (hlevel - 1)
					curfile.write(new_h + " " + m[2] + "\n")
			else:
				curfile.write(line)
	curfile.close()
	
	# Change the first line of the 'modules.rst' to be API Reference
	print("Modifying modules.rst")
	modfile = os.path.join(root_dir, "source", "reference", "modules.rst")
	bakfile = os.path.join(root_dir, "source", "reference", "modules.rst.backup")
	shutil.copyfile(modfile, bakfile)
	with open(bakfile, 'r') as fb:
		with open(modfile, 'w') as fm:
			for _ in range(2):
				fb.readline() # discarded
			title = "API Reference"
			fm.write(title + "\n")
			fm.write(("=" * len(title)) + "\n")
			shutil.copyfileobj(fb, fm)