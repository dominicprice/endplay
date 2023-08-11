import os
import re


def setup(app):
    app.connect("builder-inited", builder_inited)
    app.add_config_value("readme_module_dir", None, "env", [str])
    app.add_config_value("readme_output_dir", None, "env", [str])


def builder_inited(app):
    # Read the markdown file and create files based on the
    # section headers
    output_dir = app.config.readme_output_dir
    module_dir = app.config.readme_module_dir
    newsection = re.compile(r"^(#+)\s+(.*)$")
    os.makedirs(output_dir, exist_ok=True)
    print(f"Creating file {output_dir}/intro.md")
    sec = 1
    skip = False
    curfile = open(
        os.path.join(output_dir, f"{sec:02d}_intro.md"), "w", encoding="utf-8"
    )
    sec += 1
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
                        if m[2] == "Table of Contents":
                            skip = True
                            continue
                        else:
                            skip = False
                        curfile.close()
                        name = m[2].replace(" ", "_").lower()
                        print(f"Creating file {output_dir}/{name}.md")
                        curfile = open(
                            os.path.join(output_dir, f"{sec:02d}_{name}.md"),
                            "w",
                            encoding="utf-8",
                        )
                        sec += 1
                        curfile.write("# " + m[2] + "\n")
                    else:
                        new_h = "#" * (hlevel - 1)
                        curfile.write(new_h + " " + m[2] + "\n")
                else:
                    if not skip:
                        curfile.write(line)
    curfile.close()
