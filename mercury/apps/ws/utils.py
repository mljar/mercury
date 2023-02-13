import json
import logging
import platform

from widgets.manager import WidgetsManager

log = logging.getLogger(__name__)


CLIENT_SITE = "client"
WORKER_SITE = "worker"


def machine_uuid():
    return platform.node()


def client_group(notebook_id, session_id):
    return f"{CLIENT_SITE}-{notebook_id}-{session_id}"


def worker_group(notebook_id, session_id):
    return f"{WORKER_SITE}-{notebook_id}-{session_id}"


def is_presentation(nb):
    for cell in nb["cells"]:
        if "slideshow" in cell.get("metadata", {}):
            return True
    return False


def parse_params(nb, params={}):
    # nb in nbformat

    all_model_ids = []

    cell_counter = 1

    no_outputs = True

    for cell in nb["cells"]:
        for output in cell.get("outputs", []):
            if "data" in output and "application/mercury+json" in output["data"]:
                no_outputs = False
                view = output["data"]["application/mercury+json"]
                view = json.loads(view)

                # print(
                #    f'model_id={view.get("model_id", "")} in all models ids {all_model_ids}'
                # )

                # check model_id duplicates
                if view.get("model_id", "") in all_model_ids:
                    continue

                widget_type = view.get("widget")
                if widget_type is None:
                    continue
                else:
                    params["version"] = "2"
                    if "params" not in params:
                        params["params"] = {}

                widget_key = view.get("code_uid")
                if widget_key is None:
                    continue
                # fix cell index, cell index is not set in Jupyter Notebook mode
                widget_key = WidgetsManager.fix_cell_index(widget_key, cell_counter)

                if widget_type == "App":
                    if view.get("title") is not None:
                        params["title"] = view.get("title")
                    if view.get("description") is not None:
                        params["description"] = view.get("description")
                    if view.get("show_code") is not None:
                        params["show-code"] = view.get("show_code")
                    if view.get("show_prompt") is not None:
                        params["show-prompt"] = view.get("show_prompt")
                    if view.get("share") is not None:
                        params["share"] = view.get("share")
                    if view.get("output") is not None:
                        params["output"] = view.get("output")
                    if view.get("slug") is not None:
                        params["slug"] = view.get("slug")
                    if view.get("schedule") is not None:
                        params["schedule"] = view.get("schedule")
                    if view.get("notify") is not None:
                        params["notify"] = json.loads(view.get("notify"))
                    if view.get("continuous_update") is not None:
                        params["continuous_update"] = view.get("continuous_update")
                    if view.get("static_notebook") is not None:
                        params["static_notebook"] = view.get("static_notebook")

                else:
                    params["params"][widget_key] = WidgetsManager.frontend_format(view)

                all_model_ids += [view.get("model_id", "")]

        cell_counter += 1

    if params.get("show-code") is None:
        params["show-code"] = False
    if params.get("show-prompt") is None:
        params["show-prompt"] = True
    if params.get("continuous_update") is None:
        params["continuous_update"] = True
    if params.get("static_notebook") is None:
        params["static_notebook"] = False
    if params.get("share") is None:
        params["share"] = "public"

    if no_outputs:
        params["version"] = "2"
        params["show-code"] = False
        params["show-prompt"] = False
        params["params"] = {}
        params["output"] = "app"

    if is_presentation(nb):
        params["output"] = "slides"
