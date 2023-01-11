import json

import ipywidgets
from IPython.display import display

from .manager import WidgetsManager


class Checkbox:
    def __init__(self, value=True, label=""):
        self.code_uid = WidgetsManager.get_code_uid("Checkbox")
        if WidgetsManager.widget_exists(self.code_uid):
            self.checkbox = WidgetsManager.get_widget(self.code_uid)
            self.checkbox.description = label
        else:
            self.checkbox = ipywidgets.Checkbox(
                value=value, description=label, style={"description_width": "initial"}
            )
            WidgetsManager.add_widget(
                self.checkbox.model_id, self.code_uid, self.checkbox
            )
        display(self)

    @property
    def value(self):
        return self.checkbox.value

    @value.setter
    def value(self, v):
        self.checkbox.value = v

    def __str__(self):
        return "mercury.Checkbox"

    def __repr__(self):

        return "mercury.Checkbox"

    def _repr_mimebundle_(self, **kwargs):
        # data = {}
        # data["text/plain"] = repr(self)
        # return data
        data = self.checkbox._repr_mimebundle_()

        if len(data) > 1:
            view = {
                "widget": "Checkbox",
                "value": self.checkbox.value,
                "label": self.checkbox.description,
                "model_id": self.checkbox.model_id,
                "code_uid": self.code_uid,
            }
            data["application/mercury+json"] = json.dumps(view, indent=4)
            if "text/plain" in data:
                del data["text/plain"]

            return data
