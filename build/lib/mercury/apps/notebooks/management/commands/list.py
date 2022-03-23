import os

from django.core.management.base import BaseCommand, CommandError

from apps.notebooks.models import Notebook


class Command(BaseCommand):
    help = "List all notebooks"

    def handle(self, *args, **options):
        notebooks = Notebook.objects.all()
        if not notebooks:
            self.stdout.write(self.style.NOTICE("No notebooks available"))
        else:
            self.stdout.write(self.style.SUCCESS("Notebooks list:"))
            for n in notebooks:
                print(f"(id:{n.id}) {n.title} from {n.path}")
