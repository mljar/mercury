import json

import ipywidgets
from IPython.display import display

from .manager import WidgetsManager


class Select:
    def __init__(
        self, value=None, choices=[], label="", url_key="", disabled=False, hidden=False
    ):
        if value is None and len(choices) > 1:
            value = choices[0]

        self.code_uid = WidgetsManager.get_code_uid("Select", key=url_key)
        self.url_key = url_key
        self.hidden = hidden
        choices = [i for i in list(choices) if isinstance(i, str)]

        if WidgetsManager.widget_exists(self.code_uid):
            self.dropdown = WidgetsManager.get_widget(self.code_uid)
            if list(self.dropdown.options) != choices:
                self.dropdown.options = choices
                self.dropdown.value = value
            self.dropdown.description = label
            self.dropdown.disabled = disabled
        else:
            self.dropdown = ipywidgets.Dropdown(
                value=value,
                options=choices,
                description=label,
                style={"description_width": "initial"},
                disabled=disabled,
            )
            WidgetsManager.add_widget(
                self.dropdown.model_id, self.code_uid, self.dropdown
            )
        display(self)

    @property
    def value(self):
        return self.dropdown.value

    def __str__(self):
        return "m.Select"

    def __repr__(self):
        return "mercury.Select"

    def _repr_mimebundle_(self, **kwargs):
        # data = {}
        # data["text/plain"] = repr(self)
        # return data
        data = self.dropdown._repr_mimebundle_()

        if len(data) > 1:
            view = {
                "widget": "Select",
                "value": self.dropdown.value,
                "choices": self.dropdown.options,
                "label": self.dropdown.description,
                "model_id": self.dropdown.model_id,
                "code_uid": self.code_uid,
                "url_key": self.url_key,
                "disabled": self.dropdown.disabled,
                "hidden": self.hidden,
            }
            data["application/mercury+json"] = json.dumps(view, indent=4)
            if "text/plain" in data:
                del data["text/plain"]

            if self.hidden:
                key = "application/vnd.jupyter.widget-view+json"
                if key in data:
                    del data[key]

            return data
