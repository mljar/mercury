import json

import ipywidgets
from IPython.display import display

from .manager import WidgetsManager


class MultiSelect:
    def __init__(self, value=[], choices=[], label=""):
        if value is None and len(choices) > 1:
            value = [choices[0]]

        self.code_uid = WidgetsManager.get_code_uid("MultiSelect")

        if WidgetsManager.widget_exists(self.code_uid):
            self.select = WidgetsManager.get_widget(self.code_uid)
            if list(self.select.options) != choices:
                self.select.options = choices
                self.select.value = value
            self.select.description = label
        else:
            self.select = ipywidgets.SelectMultiple(
                value=value,
                options=choices,
                description=label,
                style={"description_width": "initial"},
            )
            WidgetsManager.add_widget(self.select.model_id, self.code_uid, self.select)
        display(self)

    @property
    def value(self):
        return list(self.select.value)

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
                "code_uid": self.code_uid,
            }
            data["application/mercury+json"] = json.dumps(view, indent=4)
            if "text/plain" in data:
                del data["text/plain"]

            return data
