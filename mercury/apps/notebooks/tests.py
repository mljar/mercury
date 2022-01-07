import os
import tempfile
import nbformat as nbf
from django.test import TestCase
from apps.notebooks.models import Notebook
from apps.notebooks.tasks import task_init_notebook

# python manage.py test apps


def create_notebook_without_yaml(filename):
    nb = nbf.v4.new_notebook()
    text = "# Title"
    code = "print(1)"
    nb["cells"] = [nbf.v4.new_markdown_cell(text), nbf.v4.new_code_cell(code)]
    with open(filename, "w") as f:
        nbf.write(nb, f)


class InitNotebookTestCase(TestCase):
    def test_init_notebook_without_yaml(self):

        with tempfile.NamedTemporaryFile() as tmp:
            create_notebook_without_yaml(tmp.name + ".ipynb")
            task_init_notebook(tmp.name + ".ipynb")
            # in the case of missing YAML
            # notebook title should be the same as filename
            nb = Notebook.objects.get(pk=1)
            self.assertEqual(nb.title, os.path.basename(tmp.name))

    def test_task_init_notebook(self):
        task_init_notebook(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "fixtures",
                "simple_notebook.ipynb",
            )
        )
