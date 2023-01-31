import json
import os
import tempfile

import ipywidgets
from IPython.display import display

from .manager import WidgetsManager


class File:
    def __init__(self, label="File upload", max_file_size="100MB"):
        self.max_file_size = max_file_size
        self.code_uid = WidgetsManager.get_code_uid("File")

        if WidgetsManager.widget_exists(self.code_uid):
            self.file = WidgetsManager.get_widget(self.code_uid)
            self.file.description = label
        else:
            self.file = ipywidgets.FileUpload(description=label)
            self.file.filepath = None
            self.file.filename = None
            WidgetsManager.add_widget(self.file.model_id, self.code_uid, self.file)
        display(self)

    @property
    def value(self):
        if len(self.file.value):
            return self.file.value[0].content

        if self.file.filepath is not None:
            # read that file
            with open(self.file.filepath, "rb", encoding="utf-8", errors="ignore") as fin:
                return fin.read()

        return None

    @property
    def filename(self):
        if len(self.file.value):
            return self.file.value[0].name
        if self.file.filename is not None:
            return self.file.filename
        return None

    @property
    def filepath(self):
        if self.file.filepath is not None:
            return self.file.filepath

        if (
            len(self.file.value)
            and self.filename is not None
            and self.value is not None
        ):
            # store file in temp dir
            # and return the path
            temp_dir = tempfile.TemporaryDirectory()
            self.file.filepath = os.path.join(temp_dir.name, self.filename)

            with open(self.file.filepath, "wb", encoding="utf-8", errors="ignore") as fout:
                fout.write(self.value)

            return self.file.filepath

        return None

    @value.setter
    def value(self, v):
        filename, filepath = v
        self.file.filepath = filepath
        self.file.filename = filename

    def __str__(self):
        return "mercury.File"

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
                "max_file_size": self.max_file_size,
                "label": self.file.description,
                "model_id": self.file.model_id,
                "code_uid": self.code_uid,
            }
            data["application/mercury+json"] = json.dumps(view, indent=4)
            if "text/plain" in data:
                del data["text/plain"]

            return data
