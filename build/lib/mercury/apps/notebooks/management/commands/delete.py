import os

from django.core.management.base import BaseCommand, CommandError

from apps.notebooks.models import Notebook


class Command(BaseCommand):
    help = "Delete a new notebook"

    def add_arguments(self, parser):
        parser.add_argument("notebook_path", help="Path to notebook")

    def handle(self, *args, **options):
        notebook_path = options["notebook_path"]
        notebook_path = os.path.abspath(notebook_path)
        self.stdout.write(self.style.HTTP_INFO(f"Try to delete {notebook_path}"))
        notebooks_deleted_cnt, _ = Notebook.objects.filter(path=notebook_path).delete()
        if notebooks_deleted_cnt:
            self.stdout.write(self.style.SUCCESS("Successfully deleted a notebook"))
        else:
            self.stdout.write(
                self.style.NOTICE("No notebooks with provided path deleted")
            )
