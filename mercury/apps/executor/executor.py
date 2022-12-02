import json
import nbformat
from execnb.shell import CaptureShell
from execnb.nbio import read_nb, nb2dict, write_nb, nb2str

from apps.executor.exporter import Exporter


class Executor:
    def __init__(self, notebook_path):
        self.shell = CaptureShell()
        self.notebook = read_nb(notebook_path)

    def run(self):
        for c in self.notebook.cells:
            self.shell.cell(c)

        exporter = Exporter()
        body, _ = exporter.run(nbformat.reads(nb2str(self.notebook), as_version=4))

        return body
