import os
import tempfile

import nbformat as nbf
from django.test import Client, TestCase
from execnb.nbio import dict2nb, read_nb

from apps.nb.exporter import Exporter
from apps.nb.nbrun import NbRun

# python manage.py test apps
from apps.nb.utils import one_cell_notebook, test_notebook
from apps.notebooks.models import Notebook
from apps.notebooks.tasks import task_init_notebook

# python manage.py test apps.nb


class NbTestCase(TestCase):
    def test_run_notebook(self):
        nb = test_notebook(code=["print(12)"])
        nb = dict2nb(nb)
        nbrun = NbRun()
        nbrun.run_notebook(nb)
        self.assertTrue("12" in "".join(nb.cells[0].outputs[0].text))

    def test_run_notebook(self):
        nb = test_notebook(code=["print(12)"])
        nb = dict2nb(nb)
        nbrun = NbRun()
        nbrun.run_notebook(nb)
        self.assertTrue("12" in "".join(nb.cells[0].outputs[0].text))

    def test_export_slides(self):
        nb = test_notebook(markdown=["# wow"])
        nb.cells[0]["metadata"] = {"slideshow": {"slide_type": "slide"}}
        nb = dict2nb(nb)
        nbrun = NbRun(is_presentation=True, reveal_theme="simple")
        nbrun.run_notebook(nb)
        body = nbrun.export_html(nb)
        self.assertTrue(len(body) > 0)
