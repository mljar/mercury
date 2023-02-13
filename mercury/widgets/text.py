import json

import ipywidgets
from IPython.display import display

from .manager import WidgetException, WidgetsManager


class Text:
    def __init__(self, value="", label="", rows=1):
        self.rows = rows

        self.code_uid = WidgetsManager.get_code_uid("Text")

        if WidgetsManager.widget_exists(self.code_uid):
            self.text = WidgetsManager.get_widget(self.code_uid)
            self.text.description = label
        else:
            self.text = ipywidgets.Textarea(value=value, description=label)
            WidgetsManager.add_widget(self.text.model_id, self.code_uid, self.text)
        display(self)

    @property
    def value(self):
        return self.text.value

    # @value.setter
    # def value(self, v):
    #    self.text.value = v

    def __str__(self):
        return "mercury.Text"

    def __repr__(self):

        return "mercury.Text"

    def _repr_mimebundle_(self, **kwargs):
        # data = {}
        # data["text/plain"] = repr(self)
        # return data
        data = self.text._repr_mimebundle_()

        if len(data) > 1:
            view = {
                "widget": "Text",
                "value": self.text.value,
                "rows": self.rows,
                "label": self.text.description,
                "model_id": self.text.model_id,
                "code_uid": self.code_uid,
            }
            data["application/mercury+json"] = json.dumps(view, indent=4)
            if "text/plain" in data:
                del data["text/plain"]

            return data
