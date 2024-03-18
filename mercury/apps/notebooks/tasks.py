import json
import logging
import os
import subprocess
import sys
import traceback
import uuid
from datetime import datetime
from shutil import which
from subprocess import PIPE, Popen

import nbformat
from allauth.account.admin import EmailAddress
from celery import shared_task
from croniter import croniter
from django.conf import settings
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from django.utils.timezone import make_aware

from apps.accounts.models import Site, SiteStatus
from apps.nb.exporter import Exporter
from apps.notebooks.models import Notebook
from apps.storage.s3utils import S3
from apps.tasks.models import Task
from apps.tasks.notify import validate_notify
from apps.ws.utils import parse_params, is_presentation

# from apps.tasks.export_png import to_png

log = logging.getLogger(__name__)


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


def nb_default_title(nb_path):
    try:
        fname = os.path.basename(nb_path)
        if "." in fname:
            return ".".join(fname.split(".")[:-1])
        return fname
    except Exception as e:
        log.exception("Problem when get default title from notebook")

    return "Please provide title"


def make_unique(slug):
    previous_slugs = Notebook.objects.values_list("slug", flat=True)
    if slug not in previous_slugs:
        return slug
    for i in range(1000000):
        slug_unique = f"{slug}-{i}"
        if slug_unique not in previous_slugs:
            return slug_unique

    return slug


def task_init_notebook(
    notebook_path,
    render_html=True,
    is_watch_mode=False,
    notebook_id=None,
    bucket_key=None,
    site=None,
    user=None,
):
    try:
        params = {
            "title": "",
            "author": "Please provide author",
            "description": "Please provide description",
            "output": "app",
            "format": {},
            "schedule": "",
            "notify": {},
        }
        nb = None
        log.info(f"Read notebook from {notebook_path}")
        with open(notebook_path, encoding="utf-8", errors="ignore") as f:
            nb = nbformat.read(f, as_version=4)
            parse_params(nb, params)

        if nb is None:
            raise Exception(f"Cant read notebook from {notebook_path}")

        if "date" in params:
            params["date"] = str(params["date"])

        notebook_title = params.get("title", "")
        if notebook_title == "":
            notebook_title = nb_default_title(notebook_path)
        notebook_output = params.get("output", "app")
        notebook_format = params.get("format", {})
        notebook_schedule = params.get("schedule", "")
        notebook_notify = params.get("notify", {})

        if is_presentation(nb):
            # automatically detect slides in cells
            # and set slides output
            notebook_output = "slides"

        if notebook_schedule != "":
            try:
                croniter.is_valid(notebook_schedule)
            except Exception as e:
                raise Exception(
                    f"The schedule ({notebook_schedule}) is not valid. {str(e)} Please check schedule at https://crontab.guru"
                )

        notebook_slug = "some-slug"
        if notebook_id is None:
            notebook_slug = params.get("slug", "")
            if notebook_slug == "":
                fname = os.path.basename(notebook_path)
                fname = fname.replace(".ipynb", "")
                notebook_slug = slugify(fname)
                if notebook_slug is None or notebook_slug == "":
                    notebook_slug = f"nb-{get_hash()}"

            notebook_slug = make_unique(notebook_slug)
        else:
            tmp_nb = Notebook.objects.get(pk=notebook_id)
            notebook_slug = tmp_nb.slug

        notebook_output_file = notebook_slug
        if notebook_id is not None:
            notebook_output_file = f"{notebook_slug}-{get_hash()}"

        if render_html:
            exporter = Exporter(
                show_code=params.get("show-code", False),
                show_prompt=params.get("show-prompt", False),
                is_presentation=notebook_output == "slides",
                reveal_theme=notebook_format.get("theme", "white"),
            )
            body = exporter.export(nb)

            with open(
                os.path.join(settings.MEDIA_ROOT, f"{notebook_output_file}.html"),
                "w",
                encoding="utf-8",
                errors="ignore",
            ) as fout:
                fout.write(body)

            error_msg = ""  # TODO: handle errors

            if not params.get("show-code", False):  # "--no-input" in command:
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

        parse_errors = validate_notify(notebook_notify)

        if notebook_id is None:
            if user is None:
                if not User.objects.filter(username="developer"):
                    user = User.objects.create_user(
                        username="developer",
                        email="developer@example.com",
                        password="developer",
                    )
                    EmailAddress.objects.create(
                        user=user, email=user.email, verified=True, primary=True
                    )
                else:
                    user = User.objects.get(username="developer")
            if site is None:
                if not Site.objects.filter(slug="single-site"):
                    site = Site.objects.create(
                        title="Mercury",
                        slug="single-site",
                        share=Site.PUBLIC,
                        created_by=user,
                        status=SiteStatus.READY,
                        domain=os.environ.get("MERCURY_DOMAIN", "runmercury.com"),
                        custom_domain=os.environ.get("MERCURY_CUSTOM_DOMAIN"),
                    )
                else:
                    site = Site.objects.get(slug="single-site")

            bucket_key_fname = ""
            if bucket_key is not None:
                s3 = S3()
                bucket_key_fname = bucket_key.replace(
                    "<replace>", f"{notebook_output_file}.html"
                )
                s3.upload_file(
                    os.path.join(settings.MEDIA_ROOT, f"{notebook_output_file}.html"),
                    bucket_key_fname,
                )

            notebook = Notebook(
                title=notebook_title,
                slug=notebook_slug,
                path=os.path.abspath(notebook_path),
                state="WATCH_READY" if is_watch_mode else "READY",
                params=json.dumps(params),
                default_view_path=bucket_key_fname
                if bucket_key is not None
                else os.path.join(settings.MEDIA_URL, f"{notebook_output_file}.html"),
                file_updated_at=make_aware(
                    datetime.fromtimestamp(os.path.getmtime(notebook_path))
                ),
                output=notebook_output,
                format=json.dumps(notebook_format),
                schedule=notebook_schedule,
                notify=json.dumps(notebook_notify),
                errors=parse_errors,
                created_by=user,
                hosted_on=site,
            )

            # html_file = os.path.join(settings.MEDIA_ROOT, f"{notebook_output_file}.html")
            # png_file = os.path.join(settings.MEDIA_ROOT, f"{notebook_output_file}.png")
            # print(html_file)
            # print(png_file)
            # to_png(html_file, png_file)

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
            notebook.file_updated_at = make_aware(
                datetime.fromtimestamp(os.path.getmtime(notebook_path))
            )
            notebook.output = notebook_output
            notebook.format = json.dumps(notebook_format)
            notebook.schedule = notebook_schedule
            notebook.notify = json.dumps(notebook_notify)
            notebook.errors = parse_errors

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
            print(traceback.format_exc())


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
