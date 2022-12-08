import json
import time 

import nbformat as nbf
from django.test import TestCase
from execnb.nbio import read_nb, dict2nb

from apps.executor.executor import Executor
from apps.executor.exporter import Exporter

# python manage.py test apps
from apps.executor.utils import one_cell_notebook, get_test_notebook


# python manage.py test apps.executor -v 2


class ExecutorTestCase(TestCase):
    
    def test_get_header(self):
        e = Executor()
        h = e.get_header()
        self.assertTrue(h.startswith("<head>"))
        self.assertTrue(h.endswith("</head>"))
        

    def test_execute(self):
        nb = get_test_notebook(markdown=["# test"], code=["print(1)"])

        nb = dict2nb(nb)

        start = time.time()
        e = Executor()
        body = e.run_notebook(nb, full_header=False)


        print(time.time() - start)


        #print(body)