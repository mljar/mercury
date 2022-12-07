import json

import nbformat
from execnb.nbio import nb2dict, nb2str, read_nb, write_nb
from execnb.shell import CaptureShell


import os, sys
CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(CURRENT_DIR, "..")
sys.path.insert(0, BACKEND_DIR)

from apps.executor.exporter import Exporter
import copy

from execnb.nbio import _dict2obj

class Executor:
    def __init__(self, notebook_path):
        self.shell = CaptureShell()
        self.shell.enable_matplotlib()

        self.notebook = read_nb(notebook_path)
        self.exporter = Exporter()

    def run(self):

        nb = copy.deepcopy(self.notebook)
        i = 1
        for c in nb.cells:
            self.shell.cell(c)
            #c.execution_count = i
            i += 1
            print(c)

        print(json.dumps(nb))

        body, _ = self.exporter.run(nbformat.reads(nb2str(nb), as_version=4))

        return body



e = Executor("/home/piotr/sandbox/mercury/mercury/demo.ipynb")
b = e.run()
# print(b)
with open("test.html", "w") as fout:
    fout.write(b)


# nb.cells += [
#     _dict2obj({
#         "cell_type": "code",
#         "execution_count": None,
#         "id": "7fasdfasdf",
#         "metadata": {},
#         "outputs": [],
#         "source": 'import datetime\nprint(datetime.datetime.now())\n',
#         "idx_": 3,
#     })
# ]