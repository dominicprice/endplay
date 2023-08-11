import os
import shutil


def setup(app):
    app.connect("builder-inited", builder_inited)


def builder_inited(app):
    # Change the first line of the 'modules.rst' to be API Reference
    output_dir = app.config.apidoc_output_dir
    modfile = os.path.join(output_dir, "endplay.rst")
    bakfile = os.path.join(output_dir, "endplay.rst.backup")
    print(f"Modifying file {modfile}")
    shutil.copyfile(modfile, bakfile)
    with open(bakfile, "r") as fb:
        with open(modfile, "w") as fm:
            for _ in range(2):
                fb.readline()  # discarded
            title = "API Documentation"
            fm.write(title + "\n")
            fm.write(("=" * len(title)) + "\n")
            shutil.copyfileobj(fb, fm)
