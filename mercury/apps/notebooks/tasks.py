import os
import sys
import uuid
import json
from datetime import datetime
import subprocess
from shutil import which
from subprocess import Popen, PIPE
from django.conf import settings
from django.template.defaultfilters import slugify
from celery import shared_task
import nbformat
import yaml

from apps.notebooks.models import Notebook


def get_hash():
    h = uuid.uuid4().hex.replace("-", "")
    return h[:5]


def is_tool(name):
    return which(name) is not None


def get_jupyter_bin_path():
    if is_tool("jupyter"):
        return "jupyter"
    if is_tool("jupyter.exe"):
        return "jupyter"
    if sys.executable.endswith("exe"):
        return os.path.join(os.path.dirname(sys.executable), "Scripts", "jupyter.exe")
    return os.path.join(os.path.dirname(sys.executable), "jupyter")


def available_kernels():
    command = [
        get_jupyter_bin_path(),
        "kernelspec",
        "list",
    ]
    msg = []
    with Popen(command, stdout=PIPE) as proc:
        msg = proc.stdout.read().decode("utf-8").split("\n")
    if not msg:
        return []
    kernels = []
    start_parsing = False
    for m in msg:
        if start_parsing:
            parts = m.split(" ")
            parts = [p for p in parts if p != ""]
            if len(parts) == 2:
                kernels += [parts[0]]  # parts[1] is a kernel path
        if "Available kernels:" in m:
            start_parsing = True
    # list of kernels name
    return kernels


def task_init_notebook(
    notebook_path, render_html=True, is_watch_mode=False, notebook_id=None
):

    try:

        kernels = available_kernels()

        params = {}
        nb = None
        update_notebook = False
        with open(notebook_path) as f:
            nb = nbformat.read(f, as_version=4)
            if "cells" in nb and len(nb["cells"]) > 0:
                first_cell = nb["cells"][0]["source"]
                if first_cell.startswith("---") and first_cell.endswith("---"):
                    params = yaml.safe_load(first_cell[3:-3])

            if (
                "metadata" in nb
                and "kernelspec" in nb["metadata"]
                and "name" in nb["metadata"]["kernelspec"]
            ):
                kernel_name = nb["metadata"]["kernelspec"]["name"]
                if kernel_name not in kernels:
                    print("*" * 42)
                    print(f"Your notebook kernel name is set to '{kernel_name}'.")
                    print(f"In this system available kernels are {kernels}.")
                    print("You need to provide other kernel name in the notebook.")
                    print("*" * 42)
                    print("You can do this manually, steps below:")
                    print("1. Close this script(Ctrl+C)")
                    print(
                        "2. Change the kernel name in the notebook (or add new kernel in the system)."
                    )
                    print("3. Rerun this command.")
                    print("*" * 42)
                    print("The other option:")
                    print(
                        "Please provide the selected kernel name and this script will update the kernel name in the notebook for you."
                    )

                    new_kernel_name = ""
                    for i in range(
                        3
                    ):  # you have 3 chances to provide kernel name from the list
                        print(
                            f"Please write the selected kernel name from the kernels list: {kernels}"
                        )
                        new_kernel_name = input()
                        if new_kernel_name in kernels:
                            break
                    if new_kernel_name not in kernels:
                        print("Sorry, cant update the kernel name in the notebook.")
                        print("Wrong kernel name selected.")
                        return
                    nb["metadata"]["kernelspec"]["name"] = new_kernel_name
                    update_notebook = True

        if update_notebook and nb is not None:
            with open(notebook_path, "w") as f:
                nbformat.write(nb, f)

        if "date" in params:
            params["date"] = str(params["date"])

        notebook_title = params.get("title", "")
        if notebook_title == "":
            notebook_title = os.path.basename(notebook_path)
            if notebook_title.endswith(".ipynb"):
                notebook_title = notebook_title[:-6]

        notebook_slug = slugify(notebook_title)
        notebook_output_file = notebook_slug
        if notebook_id is not None:
            notebook_output_file = f"{notebook_slug}-{get_hash()}"

        if render_html:
            command = [
                get_jupyter_bin_path(),
                "nbconvert",
                '--RegexRemovePreprocessor.patterns="^---"',
                notebook_path,
                "--output",
                notebook_output_file,
                "--output-dir",
                settings.MEDIA_ROOT,
                "--to",
                "html",
            ]
            if "show-code" in params and not params["show-code"]:
                command += ["--no-input"]
            if "show-prompt" in params and not params["show-prompt"]:
                command += ["--no-prompt"]

            p = subprocess.Popen(command)
            p.wait()

            if "--no-input" in command:
                with open(
                    os.path.join(settings.MEDIA_ROOT, f"{notebook_output_file}.html"),
                    "a",
                ) as fout:
                    fout.write(
                        """\n<style type="text/css">
.jp-mod-noOutputs {
    padding: 0px; 
}
.jp-mod-noInput {
  padding-top: 0px;
  padding-bottom: 0px;
}
</style>"""
                    )
        if notebook_id is None:
            notebook = Notebook(
                title=notebook_title,
                slug=notebook_slug,
                path=os.path.abspath(notebook_path),
                state="WATCH_READY" if is_watch_mode else "READY",
                params=json.dumps(params),
                default_view_path=os.path.join(
                    settings.MEDIA_URL, f"{notebook_output_file}.html"
                ),
                file_updated_at=datetime.utcfromtimestamp(
                    os.path.getmtime(notebook_path)
                ),
            )
        else:

            notebook = Notebook.objects.get(pk=notebook_id)
            notebook.title = notebook_title
            notebook.slug = notebook_slug
            notebook.path = os.path.abspath(notebook_path)
            notebook.state = "WATCH_READY" if is_watch_mode else "READY"
            notebook.params = json.dumps(params)
            # remove old default view
            if os.path.exists(notebook.default_view_path):
                os.remove(notebook.default_view_path)
            notebook.default_view_path = os.path.join(
                settings.MEDIA_URL, f"{notebook_output_file}.html"
            )
            notebook.file_updated_at = datetime.fromtimestamp(
                os.path.getmtime(notebook_path)
            )

        notebook.save()
        return notebook.id
    except KeyboardInterrupt:
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
    except Exception as e:
        if notebook_id is not None:
            raise e
        else:
            print("Error during notebook initialization.", str(e))


@shared_task(bind=True)
def task_watch(self, notebook_id):

    notebook = None
    try:
        notebook = Notebook.objects.get(pk=notebook_id)
        current_update_time = datetime.fromtimestamp(os.path.getmtime(notebook.path))
        notebook_updated_at = notebook.file_updated_at.replace(tzinfo=None)

        if current_update_time != notebook_updated_at and notebook.state in [
            "WATCH_READY",
            "WATCH_ERROR",
        ]:
            notebook.state = "WATCH_WAIT"
            notebook.save()
            task_init_notebook(
                notebook.path,
                render_html=True,
                is_watch_mode=True,
                notebook_id=notebook.id,
            )
    except Exception as e:
        if notebook is not None:
            notebook.state = "WATCH_ERROR"
            notebook.save()
