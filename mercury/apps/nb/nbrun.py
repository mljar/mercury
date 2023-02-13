import json
import os
import sys

import nbformat
from execnb.nbio import nb2dict, nb2str, read_nb, write_nb
from execnb.shell import CaptureShell

CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(CURRENT_DIR, "..")
sys.path.insert(0, BACKEND_DIR)

import copy

from execnb.nbio import _dict2obj, dict2nb

from apps.nb.exporter import Exporter
from apps.nb.utils import one_cell_notebook, test_notebook


class NbRun:
    def __init__(
        self,
        show_code=False,
        show_prompt=False,
        is_presentation=False,
        reveal_theme="white",
    ):
        self.exporter = Exporter(show_code, show_prompt, is_presentation, reveal_theme)
        self.shell = CaptureShell()
        try:
            self.shell.enable_matplotlib()
        except Exception as e:
            pass
        self.shell.run("from mercury import WidgetsManager")

    def set_show_code(self, new_show_code):
        self.exporter.set_show_code(new_show_code)

    def set_show_code_and_prompt(self, new_show_code, new_show_prompt):
        self.exporter.set_show_prompt(new_show_prompt)
        self.exporter.set_show_code(new_show_code)

    def set_is_presentation(self, new_value):
        self.exporter.set_is_presentation(new_value)

    def set_reveal_theme(self, new_value):
        self.exporter.set_reveal_theme(new_value)

    def run_set_cell_index(self, new_index):
        if new_index is not None:
            self.shell.run(f"WidgetsManager.set_cell_index({new_index})")

    def run_code(self, code):
        return self.shell.run(code)

    def run_cell(self, cell, counter=None):
        if cell.cell_type == "code":
            self.run_set_cell_index(counter)

            cell.outputs = []
            self.shell.cell(cell)

            if counter is not None:
                cell.execution_count = counter

    def run_notebook(self, nb):
        #
        # nb is fastai format
        #
        counter = 1
        for c in nb.cells:
            self.run_cell(c, counter)
            counter += 1

    def export_html(self, nb, full_header=True):
        body = self.exporter.export(
            nbformat.reads(nb2str(nb), as_version=4), full_header
        )

        return body

    def get_header(self):
        nb = one_cell_notebook("print(1)")
        nb = dict2nb(nb)
        e = NbRun()
        body = e.run_notebook(nb)
        index_start = body.find("<head>")
        index_end = body.find("</head>")

        if index_start != -1 and index_end != -1:
            return body[index_start : index_end + 7]
        return ""


# run it to fill cache
# other runs will be faster
nb = one_cell_notebook("print(1)")
nb = dict2nb(nb)
e = NbRun()
e.run_notebook(nb)

# NbRun = NbRun(is_presentation=True)
# nb_original = read_nb("./slides.ipynb")
# b = NbRun.run_notebook(nb_original, export_html=True)

# print(nb_original)
# print(b)
# with open("test.html", "w") as fout:
#    fout.write(b)

# nb = get_test_notebook(code=["import handcalcs.render", "\n%%render\na=1"])
# nb = dict2nb(nb)
# e = NbRun()
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
