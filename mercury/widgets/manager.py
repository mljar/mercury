import os
import uuid
import inspect
import logging

log = logging.getLogger(__name__)


mercury_widgets = {}
# widgets_mapping = {}
widget_index_to_model_id = {}
widgets_counter = 0
cell_index_to_widgets_index = {}


class WidgetException(Exception):
    pass


class WidgetsManager:
    widgets = {}  # model_id -> widget
    code2model = {}  # code generated uid  -> model_id
    cell_index = 0  # current cell index

    @staticmethod
    def rand_uid():
        if os.environ.get("RUN_MERCURY") is None:
            h = uuid.uuid4().hex.replace("-", "")
            return f"-rand{h[:8]}"
        return ""

    @staticmethod
    def set_cell_index(new_index):
        WidgetsManager.cell_index = new_index

    @staticmethod
    def get_code_uid(widget_type="widget", key=""):
        uid = f"{widget_type}.{WidgetsManager.cell_index}"
        for frame in inspect.stack():
            info = inspect.getframeinfo(frame[0])
            if info.function == "run_code":
                break
            uid += f".{info.lineno}"
        if key != "":
            uid += f".{key}"
        uid += WidgetsManager.rand_uid()
        return uid

    @staticmethod
    def fix_cell_index(code_uid, correct_cell_index):
        # remove rand uid
        code_uid = code_uid.split("-rand")[0]
        # fix cell index
        parts = code_uid.split(".")
        parts[1] = f"{correct_cell_index}"
        return ".".join(parts)

    @staticmethod
    def parse_cell_index(code_uid):
        return int(code_uid.split(".")[1])

    @staticmethod
    def parse_widget_type(code_uid):
        return code_uid.split(".")[0]

    @staticmethod
    def widget_exists(code_uid):
        return code_uid in WidgetsManager.code2model

    @staticmethod
    def get_widget(code_uid):
        model_id = WidgetsManager.code2model.get(code_uid)
        if model_id is None:
            return None
        return WidgetsManager.widgets.get(model_id)

    @staticmethod
    def add_widget(model_id, code_uid, widget):
        WidgetsManager.widgets[model_id] = widget
        WidgetsManager.code2model[code_uid] = model_id

    @staticmethod
    def update(code_uid, field, new_value):
        # returns
        # True if there was update
        # False if no update
        model_id = WidgetsManager.code2model.get(code_uid)
        if model_id is None:
            return False
        w = WidgetsManager.widgets.get(model_id)
        if w is not None:
            if getattr(w, field) != new_value:
                setattr(w, field, new_value)
                return True

        return False

    @staticmethod
    def frontend_format(output):
        widget_type = output.get("widget", "unknown")

        if widget_type == "Slider":
            return {
                "input": "slider",
                "value": output.get("value", 0),
                "min": output.get("min", 0),
                "max": output.get("max", 10),
                "step": output.get("step", 1),
                "label": output.get("label", ""),
                "url_key": output.get("url_key", ""),
                "disabled": output.get("disabled", False),
                "hidden": output.get("hidden", False),
            }
        elif widget_type == "Select":
            return {
                "input": "select",
                "value": output.get("value", ""),
                "choices": output.get("choices", []),
                "multi": False,
                "label": output.get("label", ""),
                "url_key": output.get("url_key", ""),
                "disabled": output.get("disabled", False),
                "hidden": output.get("hidden", False),
            }
        elif widget_type == "MultiSelect":
            return {
                "input": "select",
                "value": output.get("value", []),
                "choices": output.get("choices", []),
                "multi": True,
                "label": output.get("label", ""),
                "url_key": output.get("url_key", ""),
                "disabled": output.get("disabled", False),
                "hidden": output.get("hidden", False),
            }
        elif widget_type == "Range":
            return {
                "input": "range",
                "value": output.get("value", [0, 1]),
                "min": output.get("min", 0),
                "max": output.get("max", 10),
                "step": output.get("step", 1),
                "label": output.get("label", ""),
                "url_key": output.get("url_key", ""),
                "disabled": output.get("disabled", False),
                "hidden": output.get("hidden", False),
            }
        elif widget_type == "Text":
            return {
                "input": "text",
                "value": output.get("value", ""),
                "rows": output.get("rows", 1),
                "label": output.get("label", ""),
                "url_key": output.get("url_key", ""),
                "disabled": output.get("disabled", False),
                "hidden": output.get("hidden", False),
                "sanitize": output.get("sanitize", True),
            }
        elif widget_type == "File":
            return {
                "input": "file",
                "maxFileSize": output.get("max_file_size", 1),
                "label": output.get("label", ""),
                "disabled": output.get("disabled", False),
                "hidden": output.get("hidden", False),
            }
        elif widget_type == "OutputDir":
            return {
                "output": "dir",
                "value": "",
            }
        elif widget_type == "Checkbox":
            return {
                "input": "checkbox",
                "value": output.get("value", True),
                "label": output.get("label", ""),
                "url_key": output.get("url_key", ""),
                "disabled": output.get("disabled", False),
                "hidden": output.get("hidden", False),
            }
        elif widget_type == "Numeric":
            return {
                "input": "numeric",
                "value": output.get("value", 0),
                "min": output.get("min", 0),
                "max": output.get("max", 10),
                "step": output.get("step", 1),
                "label": output.get("label", ""),
                "url_key": output.get("url_key", ""),
                "disabled": output.get("disabled", False),
                "hidden": output.get("hidden", False),
            }
        elif widget_type == "Note":
            return {
                "output": "markdown",
                "value": output.get("value", ""),
            }
        elif widget_type == "Button":
            return {
                "input": "button",
                "value": output.get("value", False),
                "label": output.get("label", ""),
                "style": output.get("style", "primary"),
                "disabled": output.get("disabled", False),
                "hidden": output.get("hidden", False),
            }

        return {}
