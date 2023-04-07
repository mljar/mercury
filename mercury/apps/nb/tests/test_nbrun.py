# Please run tests with below command
# python manage.py test apps.nb.tests.test_nbrun
import os

from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from execnb.nbio import dict2nb
from apps.nb.nbrun import NbRun
from apps.nb.utils import one_cell_notebook


class NbRunTestCase(APITestCase):
    def setUp(self):
        pass

    def test_iframe_in_output(self):
        fname = "test-iframe-output.html"
        with open(fname, "w") as fout:
            fout.write("test")

        nbrun = NbRun()

        code = f"""from IPython.display import IFrame
IFrame(src="{fname}", width=100, height=100)"""

        nb = one_cell_notebook(code)
        nb = dict2nb(nb)

        nbrun.run_cell(nb.cells[0])
        self.assertTrue(fname not in nbrun.export_html(nb, full_header=False))

        os.remove(fname)
