import json

import ipywidgets
from IPython.display import display

from .manager import add_widget, get_widget_by_index, widget_index_exists


class Select:
    def __init__(self, value=None, choices=[], label=""):
        if value is None and len(choices) > 1:
            value = choices[0]

        if widget_index_exists():
            self.dropdown = get_widget_by_index()
            if list(self.dropdown.options) != choices:
                self.dropdown.options = choices
                self.dropdown.value = value
            self.dropdown.description = label
        else:
            self.dropdown = ipywidgets.Dropdown(
                value=value,
                options=choices,
                description=label,
            )
            add_widget(self.dropdown.model_id, self.dropdown)
        display(self)

    @property
    def value(self):
        return self.dropdown.value

    @value.setter
    def value(self, v):
        try:
            self.dropdown.value = v
        except Exception as e:
            if len(self.dropdown.options) > 0:
                self.dropdown.value = self.dropdown.options[0]
            else:
                self.dropdown.value = None

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
            }
            data["application/mercury+json"] = json.dumps(view, indent=4)
            if "text/plain" in data:
                del data["text/plain"]

            return data
