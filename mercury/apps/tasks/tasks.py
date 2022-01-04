import os
import sys
import json
import time
import shutil
import traceback
from subprocess import Popen, PIPE
from django.conf import settings
from apps.notebooks.tasks import get_jupyter_bin_path
from celery import shared_task
from apps.tasks.models import Task
from apps.notebooks.models import Notebook
import nbformat


def get_parameters_cell_index(cells, all_variables):
    max_cnt, max_index = 0, -1
    for i in range(max(len(cells), 10)):
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

        # validate input data
        inject_code = ""
        all_variables = []
        for k, v in widgets_params.items():
            all_variables += [k]
            use_default = True
            if k in task_params:
                if v["input"] == "numeric":
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
                        and (
                            widgets_params[k].get("min") is not None
                            and task_value >= widgets_params[k]["min"]
                        )
                        and (
                            widgets_params[k].get("max") is not None
                            and task_value <= widgets_params[k]["max"]
                        )
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
                        and (
                            widgets_params[k].get("min") is not None
                            and task_value >= widgets_params[k]["min"]
                        )
                        and (
                            widgets_params[k].get("max") is not None
                            and task_value <= widgets_params[k]["max"]
                        )
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
                        and (
                            widgets_params[k].get("min") is not None
                            and task_value[0] >= widgets_params[k]["min"]
                        )
                        and (
                            widgets_params[k].get("max") is not None
                            and task_value[0] <= widgets_params[k]["max"]
                        )
                        and (
                            widgets_params[k].get("min") is not None
                            and task_value[1] >= widgets_params[k]["min"]
                        )
                        and (
                            widgets_params[k].get("max") is not None
                            and task_value[1] <= widgets_params[k]["max"]
                        )
                    ):
                        inject_code += f"{k} = {task_value}\n"
                        use_default = False

            if use_default:
                if widgets_params[k].get("value") is not None:
                    inject_code += f'{k} = {widgets_params[k]["value"]}\n'

        new_cell = {
            "cell_type": "code",
            "execution_count": None,
            # "id": "1234",
            "metadata": {},
            "outputs": [],
            "source": inject_code,
        }

        wrk_dir = settings.MEDIA_ROOT / task.session_id
        if not os.path.exists(wrk_dir):
            try:
                os.mkdir(wrk_dir)
            except Exception as e:
                raise Exception(f"Cant create {wrk_dir}")

        # update input notebook with params from the task
        # the input notebook path should be the same as original notebook
        # so it can access data with relative paths
        wrk_input_nb_path = os.path.join(
            os.path.dirname(notebook.path), f"input_{task.id}_{task.session_id}.ipynb"
        )
        wrk_output_nb_file = f"output_{task.id}.html"

        if all_variables:
            with open(notebook.path) as f:
                nb = nbformat.read(f, as_version=4)
                if "cells" in nb and len(nb["cells"]) > 0:

                    old_parameters_index = get_parameters_cell_index(
                        nb["cells"], all_variables
                    )
                    if old_parameters_index != -1:
                        del nb["cells"][old_parameters_index]
                        nb["cells"].insert(
                            old_parameters_index, nbformat.from_dict(new_cell)
                        )
                    else:
                        nb["cells"].insert(0, nbformat.from_dict(new_cell))

                    with open(wrk_input_nb_path, "w") as f:
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
            "html",
        ]
        if "show-code" in notebook_params and not notebook_params["show-code"]:
            command += ["--no-input"]
        if "show-prompt" in notebook_params and not notebook_params["show-prompt"]:
            command += ["--no-prompt"]

        error_msg = ""
        with Popen(command, stdout=PIPE, stderr=PIPE) as proc:
            # print(proc.stdout.read())
            # print(proc.stderr.read())
            error_msg = proc.stderr.read()

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
        error_msg = "\n".join(error_lines)

        if error_msg == "":
            if "--no-input" in command:
                with open(wrk_dir / wrk_output_nb_file, "a") as fout:
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

            task.result = f"{settings.MEDIA_URL}{task.session_id}/{wrk_output_nb_file}"
            task.state = "DONE"
        else:
            task.result = error_msg
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
