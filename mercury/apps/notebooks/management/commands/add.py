from django.core.management.base import BaseCommand, CommandError
from apps.notebooks.models import Notebook
from apps.notebooks.tasks import task_init_notebook


class Command(BaseCommand):
    help = "Add a new notebook"

    def add_arguments(self, parser):
        parser.add_argument("notebook_path", help="Path to notebook")

    def handle(self, *args, **options):

        self.stdout.write(
            self.style.HTTP_INFO(f'Initialize {options["notebook_path"]}')
        )

        task_init_notebook(options["notebook_path"])

        self.stdout.write(self.style.SUCCESS("Successfully added a new notebook"))
