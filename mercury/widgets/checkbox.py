import ipywidgets
import json

from IPython.display import display

from .manager import WidgetException, add_widget, get_widget, get_widget_by_index, widget_index_exists


class Checkbox:
    def __init__(
        self, value=True, label=""
    ):
        if widget_index_exists():
            self.checkbox = get_widget_by_index()
            self.checkbox.description = label
        else:
            self.checkbox = ipywidgets.Textarea(
                value=value,
                description=label
            )
            add_widget(self.checkbox.model_id, self.checkbox)
        display(self)

    @property
    def value(self):
        return self.checkbox.value

    @value.setter
    def value(self, v):
        self.checkbox.value = v

    def __str__(self):
        return "m.Checkbox"

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
            }
            data["application/mercury+json"] = json.dumps(view, indent=4)
            if "text/plain" in data:
                del data["text/plain"]
                
            return data
