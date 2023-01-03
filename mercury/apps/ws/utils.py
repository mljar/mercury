import json
import logging

log = logging.getLogger(__name__)


CLIENT_SITE = "client"
WORKER_SITE = "worker"


def client_group(notebook_id, session_id):
    return f"{CLIENT_SITE}-{notebook_id}-{session_id}"


def worker_group(notebook_id, session_id):
    return f"{WORKER_SITE}-{notebook_id}-{session_id}"


def parse_params(nb, params={}):
    # nb in nbformat
    print("Parse notebook to construct Mercury params")
    cell_counter = 0
    widget_counter = 0
    widget_number_to_model_id = {}
    widget_number_to_cell_index = {}
    all_model_ids = []
    widget_types = {}
    for cell in nb["cells"]:
        if cell["cell_type"] == "code":
            if "outputs" in cell:
                for output in cell["outputs"]:

                    if (
                        "data" in output
                        and "application/mercury+json" in output["data"]
                    ):
                        view = output["data"]["application/mercury+json"]
                        view = json.loads(view)

                        # check model_id duplicates

                        print(
                            f'model_id={view.get("model_id", "")} in all models ids {all_model_ids}'
                        )

                        if view.get("model_id", "") in all_model_ids:
                            continue

                        widget_type = view.get("widget")
                        if widget_type is None:
                            continue
                        else:
                            params["version"] = "2"
                        widget_number = None
                        if widget_type == "App":
                            if view.get("title") is not None:
                                params["title"] = view.get("title")
                            if view.get("description") is not None:
                                params["description"] = view.get("description")
                            if view.get("show_code") is not None:
                                params["show-code"] = view.get("show_code")
                        elif widget_type == "Slider":
                            widget_number = f"w{widget_counter}"
                            widget_counter += 1
                            if "params" not in params:
                                params["params"] = {}
                            params["params"][widget_number] = {
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
                            widget_number = f"w{widget_counter}"
                            widget_counter += 1
                            if "params" not in params:
                                params["params"] = {}
                            params["params"][widget_number] = {
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

                        if widget_number is not None:
                            widget_number_to_model_id[widget_number] = view.get(
                                "model_id", ""
                            )
                            widget_number_to_cell_index[widget_number] = cell_counter
                            widget_types[widget_number] = widget_type
                        all_model_ids += [view.get("model_id", "")]

        cell_counter += 1
    return widget_number_to_model_id, widget_number_to_cell_index, widget_types
