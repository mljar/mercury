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


def parse_params(nb, params={}):
    # nb in nbformat

    all_model_ids = []
    
    cell_counter = 1

    for cell in nb["cells"]:
    
        for output in cell.get("outputs",[]):

            if (
                "data" in output
                and "application/mercury+json" in output["data"]
            ):
                view = output["data"]["application/mercury+json"]
                view = json.loads(view)

                # check model_id duplicates

                #print(
                #    f'model_id={view.get("model_id", "")} in all models ids {all_model_ids}'
                #)

                if view.get("model_id", "") in all_model_ids:
                    continue

                widget_type = view.get("widget")
                if widget_type is None:
                    continue
                else:
                    params["version"] = "2"
                
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
                elif widget_type == "Slider":
                    
                    if "params" not in params:
                        params["params"] = {}
                    
                    params["params"][widget_key] = {
                        "input": "slider",
                        "value": view.get("value", 0),
                        "min": view.get("min", 0),
                        "max": view.get("max", 10),
                        "label": view.get("label", ""),
                    }
                elif widget_type == "Select":
                    widget_number = f"w{widget_counter}"
                    widget_counter += 1
                    if "params" not in params:
                        params["params"] = {}
                    params["params"][widget_number] = {
                        "input": "select",
                        "value": view.get("value", ""),
                        "choices": view.get("choices", []),
                        "multi": False,
                        "label": view.get("label", ""),
                    }
                elif widget_type == "MultiSelect":
                    
                    if "params" not in params:
                        params["params"] = {}
                    params["params"][widget_key] = {
                        "input": "select",
                        "value": view.get("value", []),
                        "choices": view.get("choices", []),
                        "multi": True,
                        "label": view.get("label", ""),
                    }
                elif widget_type == "Range":
                    widget_number = f"w{widget_counter}"
                    widget_counter += 1
                    if "params" not in params:
                        params["params"] = {}
                    params["params"][widget_number] = {
                        "input": "range",
                        "value": view.get("value", [0, 1]),
                        "min": view.get("min", 0),
                        "max": view.get("max", 10),
                        "label": view.get("label", ""),
                    }
                elif widget_type == "Text":
                    widget_number = f"w{widget_counter}"
                    widget_counter += 1
                    if "params" not in params:
                        params["params"] = {}
                    params["params"][widget_number] = {
                        "input": "text",
                        "value": view.get("value", ""),
                        "rows": view.get("rows", 1),
                        "label": view.get("label", ""),
                    }
                elif widget_type == "File":
                    widget_number = f"w{widget_counter}"
                    widget_counter += 1
                    if "params" not in params:
                        params["params"] = {}
                    params["params"][widget_number] = {
                        "input": "file",
                        "maxFileSize": view.get("max_file_size", 1),
                        "label": view.get("label", ""),
                    }
                elif widget_type == "OutputDir":
                    widget_number = f"w{widget_counter}"
                    widget_counter += 1
                    if "params" not in params:
                        params["params"] = {}
                    params["params"][widget_number] = {
                        "output": "dir",
                    }
                elif widget_type == "Checkbox":
                    widget_number = f"w{widget_counter}"
                    widget_counter += 1
                    if "params" not in params:
                        params["params"] = {}
                    params["params"][widget_number] = {
                        "input": "checkbox",
                        "value": view.get("value", True),
                        "label": view.get("label", ""),
                    }
                elif widget_type == "Numeric":
                    widget_number = f"w{widget_counter}"
                    widget_counter += 1
                    if "params" not in params:
                        params["params"] = {}
                    params["params"][widget_number] = {
                        "input": "numeric",
                        "value": view.get("value", 0),
                        "min": view.get("min", 0),
                        "max": view.get("max", 10),
                        "step": view.get("step", 1),
                        "label": view.get("label", ""),
                    }

                all_model_ids += [view.get("model_id", "")]

        cell_counter += 1


    if params.get("version", "") == "2":
        if params.get("show-code") is None:
            params["show-code"] = False
        if params.get("show-prompt") is None:
            params["show-prompt"] = False
        #if params.get("output") is None:
        #    params["output"] = "app"
