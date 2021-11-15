import re
import os

def setup(app):
	app.connect('builder-inited', builder_inited)
	app.add_config_value('readme_module_dir', None, 'env', [str])
	app.add_config_value('readme_output_dir', None, 'env', [str])
	
def builder_inited(app):
	# Read the markdown file and create files based on the 
	# section headers
	output_dir = app.config.readme_output_dir
	module_dir = app.config.readme_module_dir
	newsection = re.compile(r"^(#+)\s+(.*)$")
	os.makedirs(output_dir, exist_ok = True)
	print(f"Creating file {output_dir}/intro.md")
	curfile = open(os.path.join(output_dir, "intro.md"), 'w', encoding="utf-8")
	in_code_block = False
	with open(os.path.join(module_dir, "README.md"), encoding="utf-8") as f:
		for line in f:
			if line.lstrip().startswith("```"):
				in_code_block = not in_code_block
			if in_code_block:
				curfile.write(line)
			else:
				m = newsection.match(line)
				if m:
					hlevel = len(m[1])
					if hlevel == 1:
						curfile.write("# What is endplay?\n")
					elif hlevel == 2:
						curfile.close()
						name = m[2].replace(" ", "_").lower()
						print(f"Creating file {output_dir}/{name}.md")
						curfile = open(os.path.join(output_dir, name + ".md"), 'w', encoding="utf-8")
						curfile.write("# " + m[2] + "\n")
					else:
						new_h = "#" * (hlevel - 1)
						curfile.write(new_h + " " + m[2] + "\n")
				else:
					curfile.write(line)
	curfile.close()
