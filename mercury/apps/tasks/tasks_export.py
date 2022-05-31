import json
import os
import shutil
import sys
import time
import traceback
from re import sub
from shutil import copyfile
from subprocess import PIPE, Popen

import nbformat
from celery import shared_task
from django.conf import settings
from django_drf_filepond.models import TemporaryUpload

from apps.notebooks.models import Notebook
from apps.notebooks.tasks import get_jupyter_bin_path, process_nbconvert_errors
from apps.tasks.clean_service import clean_service
from apps.tasks.models import Task
from apps.notebooks.slides_themes import SlidesThemes
from apps.tasks.export_pdf import to_pdf
from apps.tasks.notify import notify


@shared_task(bind=True)
def export_to_pdf(self, job_params):
    notebook_id = job_params.get("notebook_id")
    notebook_path = job_params.get("notebook_path")

    if notebook_id is None or notebook_path is None:
        raise Exception(
            "PDF export params validation error. Wrong notebook information."
        )

    # try to build platform independent path

    notebook_os_path = os.path.join(
        *(
            [settings.MEDIA_ROOT]
            + notebook_path.replace(settings.MEDIA_URL, "", 1).split("/")
        )
    )

    if not os.path.exists(notebook_os_path):
        raise Exception(
            f"PDF export notebook error. The notebook in HTML format does not exist."
        )

    notebook = Notebook.objects.get(pk=notebook_id)

    slides_postfix = ""
    if notebook.output == "slides":
        slides_postfix = "?print-pdf"

    pdf_os_path = notebook_os_path.replace(".html", ".pdf")

    to_pdf(notebook_os_path + slides_postfix, pdf_os_path)

    title = notebook.slug + ".pdf"

    pdf_url = notebook_path.replace(".html", ".pdf")

    return pdf_url, title
