#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import django
import json
import subprocess
import webbrowser

from glob import glob
from django.core.management.utils import get_random_secret_key

CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(CURRENT_DIR, "mercury")
sys.path.insert(0, BACKEND_DIR)

from demo import create_demo_notebook

__version__ = "1.99.1"

from widgets.manager import WidgetsManager
from widgets.app import App
from widgets.slider import Slider
from widgets.select import Select
from widgets.range import Range
from widgets.text import Text
from widgets.file import File
from widgets.checkbox import Checkbox
from widgets.numeric import Numeric
from widgets.multiselect import MultiSelect
from widgets.outputdir import OutputDir
from widgets.note import Note
from widgets.button import Button

VERBOSE = 0  # can be 0,1,2,3; 0 is no output


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

    run_add_notebook = None
    if "run" in sys.argv:
        if os.environ.get("ALLOWED_HOSTS") is None:
            os.environ["ALLOWED_HOSTS"] = "*"
        if os.environ.get("SERVE_STATIC") is None:
            os.environ["SERVE_STATIC"] = "True"
        if os.environ.get("NOTEBOOKS") is None:
            os.environ["NOTEBOOKS"] = "*.ipynb"
        if os.environ.get("WELCOME") is None:
            os.environ["WELCOME"] = "welcome.md"
        if os.environ.get("SECRET_KEY") is None:
            os.environ["SECRET_KEY"] = get_random_secret_key()
        i = sys.argv.index("run")
        sys.argv[i] = "runserver"
        sys.argv.append("--runworker")
        logo = """                            

     _ __ ___   ___ _ __ ___ _   _ _ __ _   _ 
    | '_ ` _ \ / _ \ '__/ __| | | | '__| | | |
    | | | | | |  __/ | | (__| |_| | |  | |_| |
    |_| |_| |_|\___|_|  \___|\__,_|_|   \__, |
                                         __/ |
                                        |___/ 
        """
        print(logo)

        if "demo" in sys.argv:
            create_demo_notebook("demo.ipynb")
            sys.argv.remove("demo")
            run_add_notebook = "demo.ipynb"
        else:
            for l in sys.argv:
                if l.endswith(".ipynb"):
                    run_add_notebook = l

    if "--noadditional" not in sys.argv:
        execute_from_command_line(["mercury.py", "migrate", "-v", 0])

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
            execute_from_command_line(
                ["mercury.py", "collectstatic", "--noinput", "-v", "0"]
            )
        if os.environ.get("NOTEBOOKS") is not None and run_add_notebook is None:
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

        if run_add_notebook is not None:
            execute_from_command_line(["mercury.py", "add", run_add_notebook])
            if run_add_notebook in sys.argv:
                sys.argv.remove(run_add_notebook)

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
                # "--loglevel=debug",
                "-P",
                "gevent",
                "--concurrency",
                "1",
                "-E",
            ]
            worker = subprocess.Popen(
                worker_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            # celery worker beat for periodic tasks
            beat_command = [
                "celery",
                "-A",
                "mercury.server" if sys.argv[0].endswith("mercury") else "server",
                "beat",
                "--loglevel=error",
                "--max-interval",
                "60",  # sleep 60 seconds
            ]
            subprocess.Popen(
                beat_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

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
            try:
                # open web browser if we are running a server
                url = "http://127.0.0.1:8000"
                webbrowser.open(url)
            except Exception as e:
                pass

        execute_from_command_line(arguments)

    except KeyboardInterrupt:
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
    except Exception as e:
        print("Mercury error.", str(e))


if __name__ == "__main__":
    main()
