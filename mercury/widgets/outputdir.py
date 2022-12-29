import os
import json
import tempfile
import ipywidgets

from IPython.display import display

from .manager import (
    WidgetException,
    add_widget,
    get_widget,
    get_widget_by_index,
    widget_index_exists,
)


class OutputDir:
    def __init__(self):
        self.value = "."
        

    @property
    def value(self):
        return self.value

    @property
    def filepath(self):
        return self.value

    @value.setter
    def value(self, v):
        self.value = v

    def __str__(self):
        return "mercury.OutputDir"

    def __repr__(self):
        return "mercury.OutputDir"

    def _repr_mimebundle_(self, **kwargs):
        
        data = {}
    
        view = {
            "widget": "OutputDir",        
        }
        data["application/mercury+json"] = json.dumps(view, indent=4)
        

        return data
