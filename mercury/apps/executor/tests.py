from django.test import TestCase


import nbformat as nbf

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

        e = Exporter()

        body, resources = e(nb)

        #print(body)
        #print(resources)

        with open("test.html", "w") as fout:
            fout.write(body)