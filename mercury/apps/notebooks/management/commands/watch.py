import os
import sys
import time
import subprocess
from django.core.management.base import BaseCommand, CommandError
from apps.notebooks.models import Notebook
from apps.notebooks.tasks import task_init_notebook

import psutil


def kill(proc_pid):
    try:
        process = psutil.Process(proc_pid)
        for proc in process.children(recursive=True):
            proc.kill()
        process.kill()
    except Exception as e:
        pass


class Command(BaseCommand):
    help = "Watch notebook"

    def add_arguments(self, parser):
        parser.add_argument("notebook_path", help="Path to notebook")

    def handle(self, *args, **options):
        try:

            self.stdout.write(
                self.style.HTTP_INFO(f'Watch notebook {options["notebook_path"]}')
            )

            notebook_id = task_init_notebook(
                options["notebook_path"], is_watch_mode=True
            )

            server_command = [
                sys.executable,
                sys.argv[0],
                "runserver",
            ]
            server = subprocess.Popen(server_command)

            worker_command = [
                "celery",
                "-A",
                "mercury.server" if sys.argv[0].endswith("mercury") else "server",
                "worker",
                "--loglevel=error",
                "-P",
                "gevent",
                "--concurrency",
                "1",
                "-E",
            ]
            worker = subprocess.Popen(worker_command)

            server.wait()
            worker.wait()

        except KeyboardInterrupt:
            try:
                kill(server.pid)
                kill(worker.pid)
                self.delete_notebook(notebook_id)
                self.stdout.write(self.style.SUCCESS("Stop watching"))
                sys.exit(0)
            except SystemExit:
                os._exit(0)
        except Exception as e:
            print("Notebook watch error.", str(e))

    def delete_notebook(self, id):
        Notebook.objects.filter(pk=id).delete()
        self.stdout.write(self.style.HTTP_INFO(f"Notebook deleted"))
