import json
import os
import subprocess
import sys
import uuid
from datetime import datetime
from shutil import which
from subprocess import PIPE, Popen

import nbformat
import yaml
from celery import shared_task
from django.conf import settings
from django.template.defaultfilters import slugify
from django.utils.timezone import make_aware

from apps.notebooks.models import Notebook
from apps.tasks.models import Task
from apps.notebooks.slides_themes import SlidesThemes

from croniter import croniter


def process_nbconvert_errors(error_msg):
    known_warnings = [
        "warn(",
        "UserWarning",
        "FutureWarning",
        "[NbConvertApp] Converting notebook",
        "[NbConvertApp] Writing",
    ]
    error_lines = []
    for e in error_msg.decode("utf-8").split("\n"):
        if e == "":
            continue
        known_warning = False
        for w in known_warnings:
            if w in e:
                known_warning = True
                break
        if not known_warning and e != "":
            error_lines += [e]
    return "\n".join(error_lines)


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

        params = {
            "title": "Please provide title",
            "author": "Please provide author",
            "description": "Please provide description",
            "share": "public",
            "output": "app",
            "format": {},
            "schedule": "",
        }
        nb = None
        update_notebook = False
        with open(notebook_path, encoding="utf-8", errors="ignore") as f:
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

                    if len(kernels) > 0:
                        print(f"The script will change the kernel name to {kernels[0]}")
                        new_kernel_name = kernels[0]
                        nb["metadata"]["kernelspec"]["name"] = new_kernel_name
                        update_notebook = True
                    else:
                        print(
                            "Sorry, cant automatically update the kernel name in the notebook."
                        )
                        return

        if update_notebook and nb is not None:
            with open(notebook_path, "w", encoding="utf-8", errors="ignore") as f:
                nbformat.write(nb, f)

        if "date" in params:
            params["date"] = str(params["date"])

        notebook_title = params.get("title", "Please provide title")
        if notebook_title is None or notebook_title == "":
            notebook_title = "Please provide title"
        notebook_share = params.get("share", "public")
        notebook_output = params.get("output", "app")
        notebook_format = params.get("format", {})
        notebook_schedule = params.get("schedule", "")

        if notebook_schedule != "":
            try:
                croniter.is_valid(notebook_schedule)
            except Exception as e:
                raise Exception(
                    f"The schedule ({notebook_schedule}) is not valid. {str(e)} Please check schedule at https://crontab.guru"
                )

        # make sure that there are commas and no spaces between commas
        notebook_share = (
            "," + ",".join([i.strip() for i in notebook_share.split(",")]) + ","
        )

        notebook_slug = params.get("slug", slugify(notebook_title))
        notebook_output_file = notebook_slug
        if notebook_id is not None:
            notebook_output_file = f"{notebook_slug}-{get_hash()}"

        if render_html:
            command = [
                get_jupyter_bin_path(),
                "nbconvert",
                "--RegexRemovePreprocessor.patterns=^---",
                notebook_path,
                "--output",
                notebook_output_file,
                "--output-dir",
                settings.MEDIA_ROOT,
                "--to",
                "slides" if notebook_output == "slides" else "html",
                "--Application.log_level=40",  # 30 is default, 40 is ERROR, 50 is Critical
            ]
            if "show-code" in params and not params["show-code"]:
                command += ["--no-input"]
            if "show-prompt" in params and not params["show-prompt"]:
                command += ["--no-prompt"]

            if notebook_output == "slides":
                command += SlidesThemes.nbconvert_options(notebook_format)

            error_msg = ""
            with Popen(command, stdout=PIPE, stderr=PIPE) as proc:
                # print(proc.stdout.read())
                # print(proc.stderr.read())
                error_msg = proc.stderr.read()

            error_msg = process_nbconvert_errors(error_msg)
            if error_msg != "":
                print(error_msg)

            # change file name if needed
            if notebook_output == "slides":
                expected_fpath = os.path.join(
                    settings.MEDIA_ROOT, f"{notebook_output_file}.html"
                )
                slides_fpath = os.path.join(
                    settings.MEDIA_ROOT, f"{notebook_output_file}.slides.html"
                )
                if os.path.exists(slides_fpath):
                    os.rename(slides_fpath, expected_fpath)

            if "--no-input" in command:
                with open(
                    os.path.join(settings.MEDIA_ROOT, f"{notebook_output_file}.html"),
                    "a",
                    encoding="utf-8",
                    errors="ignore",
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

            if notebook_output == "slides":
                with open(
                    os.path.join(settings.MEDIA_ROOT, f"{notebook_output_file}.html"),
                    "a",
                    encoding="utf-8",
                    errors="ignore",
                ) as fout:
                    fout.write(SlidesThemes.additional_css(notebook_format))

        if notebook_id is None:
            notebook = Notebook(
                title=notebook_title,
                slug=notebook_slug,
                path=os.path.abspath(notebook_path),
                state="WATCH_READY" if is_watch_mode else "READY",
                share=notebook_share,
                params=json.dumps(params),
                default_view_path=os.path.join(
                    settings.MEDIA_URL, f"{notebook_output_file}.html"
                ),
                file_updated_at=make_aware(
                    datetime.fromtimestamp(os.path.getmtime(notebook_path))
                ),
                output=notebook_output,
                format=json.dumps(notebook_format),
                schedule=notebook_schedule,
            )
        else:

            notebook = Notebook.objects.get(pk=notebook_id)
            notebook.title = notebook_title
            notebook.slug = notebook_slug
            notebook.path = os.path.abspath(notebook_path)
            notebook.state = "WATCH_READY" if is_watch_mode else "READY"
            notebook.share = notebook_share
            notebook.params = json.dumps(params)
            # remove old default view
            if os.path.exists(notebook.default_view_path):
                os.remove(notebook.default_view_path)
            notebook.default_view_path = os.path.join(
                settings.MEDIA_URL, f"{notebook_output_file}.html"
            )
            notebook.file_updated_at = make_aware(
                datetime.fromtimestamp(os.path.getmtime(notebook_path))
            )
            notebook.output = notebook_output
            notebook.format = json.dumps(notebook_format)
            notebook.schedule = notebook_schedule

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
            # clear all tasks
            Task.objects.filter(notebook__id=notebook.id).delete()
            # initialize updated notebook
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
