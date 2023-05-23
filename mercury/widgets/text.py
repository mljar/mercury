import json

import ipywidgets
from IPython.display import display

from .manager import WidgetException, WidgetsManager


class Text:
    def __init__(
        self, value="", label="", rows=1, url_key="", disabled=False, hidden=False
    ):
        self.rows = rows

        self.code_uid = WidgetsManager.get_code_uid("Text", key=url_key)
        self.url_key = url_key
        self.hidden = hidden
        if WidgetsManager.widget_exists(self.code_uid):
            self.text = WidgetsManager.get_widget(self.code_uid)
            self.text.description = label
            self.text.disabled = disabled
        else:
            self.text = ipywidgets.Textarea(
                value=value, description=label, disabled=disabled
            )
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
                "url_key": self.url_key,
                "disabled": self.text.disabled,
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
