import os
import shutil
import warnings
from subprocess import run
from tempfile import mkdtemp

from endplay.dealer.actions.latex import LaTeXActions, LaTeXActionsWriter


class PDFActions(LaTeXActions):
    def open(self, fname, deals):
        return PDFActionsWriter(self, fname, deals)


class PDFActionsWriter(LaTeXActionsWriter):
    def __enter__(self):
        self.tmpdir = mkdtemp()
        self.tmpname = os.path.join(self.tmpdir, "main.tex")
        self.f = open(self.tmpname, "w")
        self.on_enter()
        return self

    def __exit__(self, *_):
        self.on_exit()
        if self.f is None:
            raise RuntimeError("temporary stream is None")
        self.f.close()

        proc = run(
            ["pdflatex", "main.tex"], cwd=self.tmpdir, input=b"", capture_output=True
        )
        if proc.returncode != 0:
            with open(self.tmpdir + "/main.log") as f:
                log = f.read()
            with open(self.tmpdir + "/main.tex") as f:
                tex = f.read()
            raise RuntimeError(
                "error running pdflatex:main.log:\n" + log + "\ninput file:\n" + tex
            )
        if self.fname is None:
            raise RuntimeError("output file must be specified for pdf actions")
        shutil.copy2(
            os.path.join(self.tmpdir, "main.pdf").encode(), self.fname.encode()
        )
        try:
            shutil.rmtree(self.tmpdir)
        except Exception as e:
            warnings.warn(
                f"Unable to remove temporary directory tree {self.tmpdir}: {e}",
                ResourceWarning,
            )
