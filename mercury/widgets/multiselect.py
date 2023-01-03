import json

import ipywidgets
from IPython.display import display

from .manager import add_widget, get_widget_by_index, widget_index_exists


class MultiSelect:
    def __init__(self, value=None, choices=[], label=""):
        if value is None and len(choices) > 1:
            value = [choices[0]]

        if widget_index_exists():
            self.select = get_widget_by_index()
            if list(self.select.options) != choices:
                self.select.options = choices
                self.select.value = value
            self.select.description = label
        else:
            self.select = ipywidgets.SelectMultiple(
                value=value,
                options=choices,
                description=label,
            )
            add_widget(self.select.model_id, self.select)
        display(self)

    @property
    def value(self):
        return self.select.value

    @value.setter
    def value(self, v):
        try:
            self.select.value = v
        except Exception as e:
            if len(self.select.options) > 0:
                self.select.value = self.select.options[0]
            else:
                self.select.value = None

    def __str__(self):
        return "m.MultiSelect"

    def __repr__(self):

        return "mercury.MultiSelect"

    def _repr_mimebundle_(self, **kwargs):
        # data = {}
        # data["text/plain"] = repr(self)
        # return data
        data = self.select._repr_mimebundle_()

        if len(data) > 1:
            view = {
                "widget": "MultiSelect",
                "value": self.select.value,
                "choices": self.select.options,
                "label": self.select.description,
                "model_id": self.select.model_id,
            }
            data["application/mercury+json"] = json.dumps(view, indent=4)
            if "text/plain" in data:
                del data["text/plain"]

            return data
