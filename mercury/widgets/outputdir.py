import json
import os
import tempfile

import ipywidgets
from IPython.display import display

from .manager import WidgetsManager


class DirPath:
    def __init__(self, dir_path):
        self.value = dir_path


class OutputDir:
    def __init__(self):
        self.code_uid = WidgetsManager.get_code_uid("OutputDir")
        if WidgetsManager.widget_exists(self.code_uid):
            self.dir_path = WidgetsManager.get_widget(self.code_uid)
        else:
            self.dir_path = DirPath(os.environ.get("MERCURY_OUTPUTDIR", "."))
            WidgetsManager.add_widget("output-dir", self.code_uid, self.dir_path)
        display(self)

    @property
    def path(self):
        return self.dir_path.value

    def __str__(self):
        return "mercury.OutputDir"

    def __repr__(self):
        return "mercury.OutputDir"

    def _repr_mimebundle_(self, **kwargs):

        data = {}

        view = {
            "widget": "OutputDir",
            "model_id": "output-dir",
            "code_uid": self.code_uid
        }
        data["application/mercury+json"] = json.dumps(view, indent=4)
        data["text/html"] = "<h3>Output Directory</h3><small>This output won't appear in the web app.</small>"
        

        return data
