import json

import ipywidgets
from IPython.display import display

from .manager import (
    WidgetException,
    add_widget,
    get_widget,
    get_widget_by_index,
    widget_index_exists,
)


class Text:
    def __init__(self, value="", label="", rows=1):
        self.rows = rows
        if widget_index_exists():
            self.text = get_widget_by_index()
            self.text.description = label
        else:
            self.text = ipywidgets.Textarea(value=value, description=label)
            add_widget(self.text.model_id, self.text)
        display(self)

    @property
    def value(self):
        return self.text.value

    @value.setter
    def value(self, v):
        self.text.value = v

    def __str__(self):
        return "m.Text"

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
            }
            data["application/mercury+json"] = json.dumps(view, indent=4)
            if "text/plain" in data:
                del data["text/plain"]

            return data
