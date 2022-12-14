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

from execnb.nbio import _dict2obj, dict2nb
from apps.executor.utils import one_cell_notebook, get_test_notebook


class Executor:
    def __init__(self, show_code=False):
        self.exporter = Exporter(show_code)
        self.shell = CaptureShell()
        try:
            self.shell.enable_matplotlib()
        except Exception as e:
            pass

    def run(self, code):
        return self.shell.run(code)

    def run_cell(self, cell, counter=None):
        if cell.cell_type == "code":
            self.shell.cell(cell)
            if counter is not None:
                cell.execution_count = counter

    def run_notebook(self, nb, export_html=True, full_header=True, show_code=False):
        counter = 1
        for c in nb.cells:
            self.shell.cell(c)
            if c.cell_type == "code":
                c.execution_count = counter
                counter += 1

        if export_html:
            return self.export_html(nb, full_header, show_code)

    def export_html(self, nb, full_header=True, show_code=False):

        body, _ = self.exporter.run(
            nbformat.reads(nb2str(nb), as_version=4), show_code=show_code
        )

        if not full_header:
            index_start = body.find("<head>")
            index_end = body.find("</head>")

            if index_start != -1 and index_end != -1:
                body = body[:index_start] + "" + body[index_end + 7 :]

                body = body.replace("<!DOCTYPE html>", "")
                body = body.replace("<html>", "")
                body = body.replace("<body ", "<div ")
                body = body.replace("</body>", "</div>")
                body = body.replace("</html>", "")

        return body

    def get_header(self):
        nb = one_cell_notebook("print(1)")
        nb = dict2nb(nb)
        e = Executor()
        body = e.run_notebook(nb)
        index_start = body.find("<head>")
        index_end = body.find("</head>")

        if index_start != -1 and index_end != -1:
            return body[index_start : index_end + 7]
        return ""


nb = one_cell_notebook("print(1)")
nb = dict2nb(nb)
e = Executor()
b = e.run_notebook(nb, show_code=False)

# with open("test.html", "w") as fout:
#    fout.write(b)

# nb = get_test_notebook(code=["import handcalcs.render", "\n%%render\na=1"])
# nb = dict2nb(nb)
# e = Executor()
# b = e.run_notebook(nb)

# # print(b)
# with open("test.html", "w") as fout:
#    fout.write(b)


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
