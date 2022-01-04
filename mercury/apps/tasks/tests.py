import os
from django.test import TestCase
from apps.notebooks.models import Notebook
from apps.tasks.models import Task
from apps.tasks.tasks import task_execute

from apps.notebooks.tasks import task_init_notebook

# python manage.py test apps.tasks.tests -v 2


class ExecuteNotebookTestCase(TestCase):
    def setUp(self):

        task_init_notebook(
            "apps/notebooks/fixtures/third_notebook.ipynb", render_html=False
        )
        # Notebook.objects.create(
        #     title="my first notebook", slug="my-first-notebook", params="test-params"
        # )

    def test_task_execute_notebook(self):

        Task.objects.create(notebook_id=1, session_id="test")

        job_params = {
            "db_id": 1,
        }

        task_execute(job_params)
