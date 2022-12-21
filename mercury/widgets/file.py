import ipywidgets
import json

from IPython.display import display

from .manager import WidgetException, add_widget, get_widget, get_widget_by_index, widget_index_exists


class File:
    def __init__(
        self, label="", max_file_size="100MB"
    ):
        self.max_file_size = max_file_size
        if widget_index_exists():
            self.file = get_widget_by_index()
            self.file.description = label
        else:
            self.file = ipywidgets.File(
                description=label
            )
            add_widget(self.file.model_id, self.file)
        display(self)

    @property
    def value(self):
        return self.file.value

    @value.setter
    def value(self, v):
        self.file.value = v

    def __str__(self):
        return "m.File"

    def __repr__(self):

        return "mercury.File"

    def _repr_mimebundle_(self, **kwargs):
        # data = {}
        # data["text/plain"] = repr(self)
        # return data
        data = self.file._repr_mimebundle_()
        
        if len(data) > 1:
            view = {
                "widget": "File",
                "value": self.file.value,
                "max_file_size": self.max_file_size,
                "label": self.file.description,
                "model_id": self.file.model_id,
            }
            data["application/mercury+json"] = json.dumps(view, indent=4)
            if "text/plain" in data:
                del data["text/plain"]
                
            return data
