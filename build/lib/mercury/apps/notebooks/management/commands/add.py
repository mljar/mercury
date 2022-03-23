import os

from django.core.management.base import BaseCommand, CommandError

from apps.notebooks.models import Notebook
from apps.notebooks.tasks import task_init_notebook


class Command(BaseCommand):
    help = "Add a new notebook"

    def add_arguments(self, parser):
        parser.add_argument("notebook_path", help="Path to notebook")

    def handle(self, *args, **options):
        notebook_path = options["notebook_path"]
        notebook_id = self.notebook_id_available(notebook_path)

        action = "added"
        if notebook_id is None:
            self.stdout.write(self.style.HTTP_INFO(f"Initialize {notebook_path}"))
        else:
            action = "updated"
            self.stdout.write(
                self.style.HTTP_INFO(f"The notebook {notebook_path} will be updated")
            )

        notebook_id = task_init_notebook(
            options["notebook_path"], notebook_id=notebook_id
        )

        self.stdout.write(
            self.style.SUCCESS(f"Successfully {action} a notebook (id:{notebook_id})")
        )

    def notebook_id_available(self, notebook_path):
        notebook = Notebook.objects.filter(path=os.path.abspath(notebook_path)).first()
        if notebook is not None:
            return notebook.id
        return None
