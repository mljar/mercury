import json

import nbformat as nbf
from django.test import TestCase

from apps.executor.executor import Executor
from apps.executor.exporter import Exporter

# python manage.py test apps


def get_test_notebook(markdown=[], code=[]):
    nb = nbf.v4.new_notebook()
    nb["cells"] = []
    for m in markdown:
        nb["cells"] += [nbf.v4.new_markdown_cell(m)]
    for c in code:
        nb["cells"] += [nbf.v4.new_code_cell(c)]

    return nb


# python manage.py test apps.executor -v 2


class ExporterTestCase(TestCase):
    def test_export(self):
        nb = get_test_notebook(markdown=["# test"], code=["print(1)"])

        # print(json.dumps(nb, indent=4))

        e = Exporter()

        body, resources = e.run(nb)

        # print(body)
        # print(resources)

        # with open("test.html", "w") as fout:
        #    fout.write(body)


class ExecutorTestCase(TestCase):
    def test_execute(self):
        nb = get_test_notebook(markdown=["# test"], code=["print(1)"])

        notebook_path = "test_execute.ipynb"
        with open(notebook_path, "w", encoding="utf-8", errors="ignore") as f:
            nbf.write(nb, f)

        e = Executor(notebook_path)
        body = e.run()
