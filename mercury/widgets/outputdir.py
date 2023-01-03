import json
import os
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


class DirPath:
    def __init__(self, dir_path):
        self.value = dir_path


class OutputDir:
    def __init__(self):
        if widget_index_exists():
            self.dir_path = get_widget_by_index()
        else:
            self.dir_path = DirPath(".")
            add_widget("output-dir", self.dir_path)
        display(self)

    # @property
    # def value(self):
    #    return self.value

    @property
    def path(self):
        return self.dir_path.value

    # @value.setter
    # def value(self, v):
    #    if self.value != v:
    #        self.value = v

    def __str__(self):
        return "mercury.OutputDir"

    def __repr__(self):
        return "mercury.OutputDir"

    def _repr_mimebundle_(self, **kwargs):

        data = {}

        view = {"widget": "OutputDir", "model_id": "output-dir"}
        data["application/mercury+json"] = json.dumps(view, indent=4)

        return data
