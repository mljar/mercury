import os
from django.test import TestCase
from apps.notebooks.models import Notebook
from apps.notebooks.tasks import task_init_notebook

# python manage.py test apps


class InitNotebookTestCase(TestCase):
    def setUp(self):
        # Notebook.objects.create(
        #     title="my first notebook",
        #     slug="my-first-notebook",
        #     ,
        # )
        pass

    def test_task_init_notebook(self):

        task_init_notebook(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "fixtures",
                "simple_notebook.ipynb",
            )
        )
