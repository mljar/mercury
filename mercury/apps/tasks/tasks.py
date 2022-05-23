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


def get_parameters_cell_index(cells, all_variables):
    max_cnt, max_index = 0, -1
    for i in range(min(len(cells), 10)):
        cnt = 0
        if cells[i]["cell_type"] == "code" and not cells[i]["source"].startswith("---"):

            for v in all_variables:
                if v in cells[i]["source"]:
                    cnt += 1
        if cnt == len(all_variables):
            return i
        if cnt > max_cnt:
            max_cnt = cnt
            max_index = i

    return max_index


def sanitize_string(input_string):
    return sub("""[\"\'(){}\[\]\`\^\:]""", "", input_string)


@shared_task(bind=True)
def task_execute(self, job_params):
    wrk_input_nb_path = None
    try:
        task = Task.objects.get(pk=job_params["db_id"])
        task.state = "RECEIVED"
        # task.task_id = self.request.get("id", "not-available") # in case of unit tests, id is None
        task.save()

        notebook = Notebook.objects.get(pk=task.notebook_id)

        task_params = {}
        if task.params:
            task_params = json.loads(task.params)

        notebook_params = json.loads(notebook.params)
        widgets_params = notebook_params.get("params", {})

        # validate input variables
        inject_code = ""
        all_variables = []
        remove_after_execution = []
        for k, v in widgets_params.items():
            all_variables += [k]
            use_default = True
            if k in task_params:
                if v["input"] == "text":
                    task_value = task_params[k]
                    inject_code += f'{k} = """{sanitize_string(task_value)}"""\n'
                    use_default = False

                elif v["input"] == "file":

                    file_server_id = task_params[k]
                    # Get the temporary upload record
                    tu = TemporaryUpload.objects.get(upload_id=file_server_id)

                    input_file = f"{task.id}_{tu.upload_name}"
                    input_path = os.path.join(
                        os.path.dirname(notebook.path), input_file
                    )
                    copyfile(tu.get_file_path(), input_path)

                    inject_code += f'{k} = "{input_file}"\n'
                    use_default = False

                    remove_after_execution += [input_path]

                    # DO NOT Delete the temporary upload record and the temporary directory
                    # the file is kept in the UI, maybe user want to reuse it one more time
                    # it will be removed later by cleaning service
                    # DO NOT tu.delete()
                elif v["input"] == "numeric":
                    task_value = task_params[k]
                    if (
                        (
                            str(task_value)
                            .replace(".", "", 1)
                            .replace(",", "")
                            .replace("-", "", 1)
                            .replace("e", "", 1)
                            .isdigit()
                        )
                        and (task_value >= widgets_params[k].get("min", 0))
                        and (task_value <= widgets_params[k].get("max", 100))
                    ):
                        inject_code += f"{k} = {task_value}\n"
                        use_default = False
                elif v["input"] == "checkbox":
                    task_value = task_params[k]
                    if task_value in [True, False]:
                        task_value = "True" if task_value else "False"
                        inject_code += f"{k} = {task_value}\n"
                        use_default = False
                elif v["input"] == "select":
                    task_value = task_params[k]
                    isMulti = widgets_params[k].get("multi", False)
                    if not isMulti and task_value in widgets_params[k]["choices"]:
                        inject_code += f'{k} = "{task_value}"\n'
                        use_default = False
                    if isMulti:
                        values_str_list = []
                        for t in task_value:
                            if t in widgets_params[k]["choices"]:
                                values_str_list += [f'"{t}"']
                        if values_str_list:
                            inject_code += f'{k} = [{",".join(values_str_list)}]\n'
                            use_default = False
                elif v["input"] == "slider":
                    task_value = task_params[k]

                    if (
                        (
                            str(task_value)
                            .replace(".", "", 1)
                            .replace(",", "")
                            .replace("-", "", 1)
                            .replace("e", "", 1)
                            .isdigit()
                        )
                        and (task_value >= widgets_params[k].get("min", 0))
                        and (task_value <= widgets_params[k].get("max", 100))
                    ):
                        inject_code += f"{k} = {task_value}\n"
                        use_default = False
                elif v["input"] == "range":
                    task_value = task_params[k]

                    if (
                        len(task_value) == 2
                        and (
                            str(task_value[0])
                            .replace(".", "", 1)
                            .replace(",", "")
                            .replace("-", "", 1)
                            .replace("e", "", 1)
                            .isdigit()
                        )
                        and (
                            str(task_value[1])
                            .replace(".", "", 1)
                            .replace(",", "")
                            .replace("-", "", 1)
                            .replace("e", "", 1)
                            .isdigit()
                        )
                        and (task_value[0] >= widgets_params[k].get("min", 0))
                        and (task_value[0] <= widgets_params[k].get("max", 100))
                        and (task_value[1] >= widgets_params[k].get("min", 0))
                        and (task_value[1] <= widgets_params[k].get("max", 100))
                    ):
                        inject_code += f"{k} = {task_value}\n"
                        use_default = False

            if use_default:
                if widgets_params[k].get("value") is not None:
                    if v["input"] in ["text", "file", "select"]:
                        inject_code += f'{k} = "{widgets_params[k].get("value", "")}"\n'
                    else:
                        inject_code += f'{k} = {widgets_params[k].get("value")}\n'

        # create output directory for notebook output
        wrk_dir = settings.MEDIA_ROOT / task.session_id
        if not os.path.exists(wrk_dir):
            try:
                os.mkdir(wrk_dir)
            except Exception as e:
                raise Exception(f"Cant create {wrk_dir}")

        # validate output variables
        for k, v in widgets_params.items():
            if v.get("output") is not None and v.get("output") == "dir":
                # create output directory for files created in the notebook
                output_dir = settings.MEDIA_ROOT / task.session_id / f"output_{task.id}"
                if not os.path.exists(output_dir):
                    try:
                        os.mkdir(output_dir)
                    except Exception as e:
                        raise Exception(f"Cant create {output_dir}")
                # pass path to directory into the notebook's code
                inject_code += f'{k} = "{str(output_dir)}"\n'

            if v.get("output") is not None and v.get("output") == "response":
                # create output directory for REST response created in the notebook
                output_dir = settings.MEDIA_ROOT / task.session_id
                if not os.path.exists(output_dir):
                    try:
                        os.mkdir(output_dir)
                    except Exception as e:
                        raise Exception(f"Cant create {output_dir}")
                # pass path to directory into the notebook's code
                output_dir = output_dir / "response.json"
                inject_code += f'{k} = "{str(output_dir)}"\n'
                print(inject_code)

        new_cell = {
            "cell_type": "code",
            "execution_count": None,
            # "id": "1234",
            "metadata": {},
            "outputs": [],
            "source": inject_code,
        }

        # update input notebook with params from the task
        # the input notebook path should be the same as original notebook
        # so it can access data with relative paths
        wrk_input_nb_path = os.path.join(
            os.path.dirname(notebook.path), f"input_{task.id}_{task.session_id}.ipynb"
        )
        wrk_output_nb_file = f"output_{task.id}.html"

        if all_variables:
            with open(notebook.path, encoding="utf-8", errors="ignore") as f:
                nb = nbformat.read(f, as_version=4)
                if "cells" in nb and len(nb["cells"]) > 0:

                    old_parameters_index = get_parameters_cell_index(
                        nb["cells"], all_variables
                    )
                    if old_parameters_index != -1 and old_parameters_index < len(
                        nb["cells"]
                    ):
                        new_cell["metadata"] = nb["cells"][old_parameters_index].get(
                            "metadata", {}
                        )
                        del nb["cells"][old_parameters_index]
                        nb["cells"].insert(
                            old_parameters_index, nbformat.from_dict(new_cell)
                        )
                    else:
                        nb["cells"].insert(0, nbformat.from_dict(new_cell))

                    with open(
                        wrk_input_nb_path, "w", encoding="utf-8", errors="ignore"
                    ) as f:
                        nbformat.write(nb, f)
        else:
            shutil.copyfile(notebook.path, wrk_input_nb_path)

        command = [
            get_jupyter_bin_path(),
            "nbconvert",
            "--RegexRemovePreprocessor.patterns='^---'",
            "--execute",
            "--allow-errors",
            str(wrk_input_nb_path),
            "--output",
            wrk_output_nb_file,
            "--output-dir",
            str(wrk_dir),
            "--to",
            "slides" if notebook.output == "slides" else "html",
        ]
        if "show-code" in notebook_params and not notebook_params["show-code"]:
            command += ["--no-input"]
        if "show-prompt" in notebook_params and not notebook_params["show-prompt"]:
            command += ["--no-prompt"]

        if notebook.output == "slides":
            command += SlidesThemes.nbconvert_options(json.loads(notebook.format))

        error_msg = ""
        with Popen(command, stdout=PIPE, stderr=PIPE) as proc:
            # print(proc.stdout.read())
            # print(proc.stderr.read())
            error_msg = proc.stderr.read()

        error_msg = process_nbconvert_errors(error_msg)

        # check if output file exists
        output_html_path = os.path.join(str(wrk_dir), wrk_output_nb_file)

        # change file name if needed
        if notebook.output == "slides":
            slides_fpath = os.path.join(
                str(wrk_dir), f"{wrk_output_nb_file}.slides.html"
            )
            if os.path.exists(slides_fpath):
                os.rename(slides_fpath, output_html_path)

        if os.path.isfile(output_html_path):
            if "--no-input" in command:
                with open(
                    wrk_dir / wrk_output_nb_file, "a", encoding="utf-8", errors="ignore"
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

            if notebook.output == "slides":
                with open(
                    wrk_dir / wrk_output_nb_file, "a", encoding="utf-8", errors="ignore"
                ) as fout:
                    fout.write(SlidesThemes.additional_css(json.loads(notebook.format)))

            task.result = f"{settings.MEDIA_URL}{task.session_id}/{wrk_output_nb_file}"
            task.state = "DONE"
        else:
            task.result = (
                error_msg if error_msg != "" else "Problem with executing the notebook"
            )
            task.state = "ERROR"
        task.save()
    except Exception as e:
        task.result = str(e)
        task.state = "ERROR"
        task.save()
        print(str(e))
        print(traceback.format_exc())
    finally:
        # remove input notebook
        if wrk_input_nb_path is not None:
            if os.path.isfile(wrk_input_nb_path):
                os.remove(wrk_input_nb_path)
        # remove copied files from temporary uploads
        for f in remove_after_execution:
            if os.path.exists(f):
                os.remove(f)
        # remove old file
        clean_service()


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
