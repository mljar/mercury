import os
import json
import logging
import platform
import requests
import nbformat

from widgets.manager import WidgetsManager

log = logging.getLogger(__name__)


CLIENT_SITE = "client"
WORKER_SITE = "worker"

# global variable
my_ip = None


def machine_uuid():
    global my_ip
    if my_ip is not None:
        return my_ip
    if os.environ.get("USE_WORKER_IP") is not None:
        try:
            # fast way to get IP
            response = requests.get("http://checkip.amazonaws.com", timeout=15)
            my_ip = response.content.decode("UTF-8").replace("\n", "")
            return my_ip

        except Exception as e:
            pass

        # alternative service
        # response = requests.get("https://api.ipify.org?format=json")
        # my_ip = response.json().get("ip", platform.node())
        # return my_ip

    my_ip = platform.node()
    return my_ip


def client_group(notebook_id, session_id):
    return f"{CLIENT_SITE}-{notebook_id}-{session_id}"


def worker_group(notebook_id, session_id):
    return f"{WORKER_SITE}-{notebook_id}-{session_id}"


def is_presentation(nb):
    for cell in nb["cells"]:
        if "slideshow" in cell.get("metadata", {}):
            if "slide_type" in cell.get("metadata").get("slideshow", {}):
                if cell.get("metadata").get("slideshow").get("slide_type") == "slide":
                    return True
    return False


def parse_params(nb, params={}):
    # nb in nbformat

    all_model_ids = []

    cell_counter = 1

    no_outputs = True

    mercury_package_imported = False

    for cell in nb["cells"]:
        if not mercury_package_imported:
            # try to guess if mercury is imported
            code = cell.get("source", "")
            if isinstance(code, list):
                code = "".join(code)
            if "mercury" in code:
                mercury_package_imported = True

        for output in cell.get("outputs", []):
            if "data" in output and "application/mercury+json" in output["data"]:
                no_outputs = False
                view = output["data"]["application/mercury+json"]

                if isinstance(view, nbformat.notebooknode.NotebookNode):
                    view = view.dict()
                else:
                    view = json.loads(str(view))

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
                    if view.get("output") is not None:
                        params["output"] = view.get("output")
                    if view.get("schedule") is not None:
                        params["schedule"] = view.get("schedule")
                    if view.get("notify") is not None:
                        params["notify"] = json.loads(view.get("notify"))
                    if view.get("continuous_update") is not None:
                        params["continuous_update"] = view.get("continuous_update")
                    if view.get("static_notebook") is not None:
                        params["static_notebook"] = view.get("static_notebook")

                    for property in [
                        "show_sidebar",
                        "full_screen",
                        "allow_download",
                        "stop_on_error",
                    ]:
                        if view.get(property) is not None:
                            params[property] = view.get(property)

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
        params["static_notebook"] = not mercury_package_imported
    if params.get("show_sidebar") is None:
        params["show_sidebar"] = True
    if params.get("full_screen") is None:
        params["full_screen"] = True
    if params.get("allow_download") is None:
        params["allow_download"] = True
    if params.get("stop_on_error") is None:
        params["stop_on_error"] = False

    if no_outputs:
        params["version"] = "2"
        params["show-code"] = False
        params["show-prompt"] = False
        params["params"] = {}
        params["output"] = "app"

    if is_presentation(nb):
        params["output"] = "slides"
