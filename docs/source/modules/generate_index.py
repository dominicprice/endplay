from itertools import takewhile
from pathlib import Path, WindowsPath


def setup(app):
    app.connect("builder-inited", builder_inited)
    app.add_config_value("index_pages_root", None, "env", [Path, WindowsPath])
    app.add_config_value("index_output_file", None, "env", [Path, WindowsPath])
    app.add_config_value("index_sections", None, "env", [list])
    app.add_config_value("index_template_file", None, "env", [Path, WindowsPath])


def builder_inited(app):
    pages_dir = app.config.index_pages_root
    root_dir = app.config.index_output_file.parent
    # Accumulate the sections
    sections = []
    for section in app.config.index_sections:
        path = Path(pages_dir, section)
        if path.is_file():
            sections.append(path.with_suffix("").relative_to(root_dir).as_posix())
        else:
            subsections = [
                f.with_suffix("").relative_to(root_dir).as_posix()
                for f in path.iterdir()
            ]
            sections += sorted(subsections)

    # tee input to output, replacing the %SECTIONS% tag with the actual sections
    infile, outfile = app.config.index_template_file, app.config.index_output_file
    with open(infile) as fin, open(outfile, "w") as fout:
        for line in fin:
            if line.strip() == "%SECTIONS%":
                indent = "".join(takewhile(str.isspace, line))
                for section in sections:
                    fout.write(indent + section + "\n")
            else:
                fout.write(line.replace("%VERSION%", app.config.release))
