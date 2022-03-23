import os
import subprocess
import sys
import time

import psutil
from django.core.management.base import BaseCommand, CommandError

from apps.notebooks.models import Notebook
from apps.notebooks.tasks import task_init_notebook


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
        parser.add_argument("notebook_path", help="Path to the notebook")

    def handle(self, *args, **options):
        try:

            self.stdout.write(
                self.style.HTTP_INFO(f'Watching notebook {options["notebook_path"]}')
            )

            notebook_id = task_init_notebook(
                options["notebook_path"], is_watch_mode=True
            )

            logo = """                                                                                  
     _ __ ___   ___ _ __ ___ _   _ _ __ _   _ 
    | '_ ` _ \ / _ \ '__/ __| | | | '__| | | |
    | | | | | |  __/ | | (__| |_| | |  | |_| |
    |_| |_| |_|\___|_|  \___|\__,_|_|   \__, |
                                         __/ |
                                        |___/ 
            """

            self.stdout.write(self.style.SUCCESS("-" * 53))
            self.stdout.write(self.style.SUCCESS(logo))
            self.stdout.write(self.style.SUCCESS("-" * 53))
            self.stdout.write(
                self.style.SUCCESS(
                    f"Please open the following address in your web browser"
                )
            )
            self.stdout.write(
                self.style.SUCCESS(f"--> http://127.0.0.1:8000/app/{notebook_id}")
            )
            self.stdout.write(self.style.SUCCESS("-" * 53))

            mercury_bin = sys.argv[0]
            # check if we are on Windows machines and
            # need to extend the mercury bin with .exe
            if sys.executable.endswith(".exe") and not mercury_bin.endswith(".exe"):
                mercury_bin += ".exe"

            server_command = [
                sys.executable,
                mercury_bin,
                "runserver",
                "--noreload",
                "--noadditional",
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
                self.clear_celery_backend()
                self.stdout.write(self.style.SUCCESS("Stop watching"))
                sys.exit(0)
            except SystemExit:
                os._exit(0)
        except Exception as e:
            print("Mercury watch error.", str(e))

    def delete_notebook(self, id):
        Notebook.objects.filter(pk=id).delete()
        self.stdout.write(self.style.HTTP_INFO(f"Notebook deleted"))

    def clear_celery_backend(self):
        try:
            if os.path.exists("celery.sqlite"):
                os.remove("celery.sqlite")
        except Exception as e:
            print("Problem with removing Celery backend", str(e))
