#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import django
import json
import subprocess
from glob import glob

CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(CURRENT_DIR, "mercury")
sys.path.insert(0, BACKEND_DIR)


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    if "--noadditional" not in sys.argv:
        execute_from_command_line(["mercury.py", "migrate"])

        superuser_username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        if (
            superuser_username is not None
            and os.environ.get("DJANGO_SUPERUSER_EMAIL") is not None
            and os.environ.get("DJANGO_SUPERUSER_PASSWORD") is not None
        ):
            try:
                from django.contrib.auth import get_user_model

                User = get_user_model()
                if not User.objects.filter(username=superuser_username):
                    execute_from_command_line(
                        ["mercury.py", "createsuperuser", "--noinput"]
                    )
            except Exception as e:
                print(str(e))
        if os.environ.get("SERVE_STATIC") is not None:
            execute_from_command_line(["mercury.py", "collectstatic", "--noinput"])
        if os.environ.get("NOTEBOOKS") is not None:
            notebooks_str = os.environ.get("NOTEBOOKS")
            notebooks = []
            if "[" in notebooks_str or "{" in notebooks_str:
                notebooks = json.loads(notebooks_str)
            elif "*" in notebooks_str:
                notebooks = glob(notebooks_str)
            else:
                notebooks = [notebooks_str]
            for nb in notebooks:
                execute_from_command_line(["mercury.py", "add", nb])

        worker = None
        if (
            os.environ.get("RUN_WORKER", "False") == "True"
            or "runworker" in sys.argv
            or "--runworker" in sys.argv
        ):
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

            if "--runworker" in sys.argv:
                sys.argv.remove("--runworker")

            if "runworker" in sys.argv:
                worker.wait()
    else:
        sys.argv.remove("--noadditional")

    try:
        arguments = sys.argv
        if (
            len(sys.argv) > 1
            and arguments[1] == "runserver"
            and "--noreload" not in arguments
        ):
            arguments += ["--noreload"]
        execute_from_command_line(arguments)
    except KeyboardInterrupt:
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
    except Exception as e:
        print("Notebook watch error.", str(e))


if __name__ == "__main__":
    main()
