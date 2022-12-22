import os
import json
import tempfile 
import ipywidgets


from django_drf_filepond.models import TemporaryUpload
from IPython.display import display

from .manager import WidgetException, add_widget, get_widget, get_widget_by_index, widget_index_exists


class File:
    def __init__(
        self, label="File upload", max_file_size="100MB"
    ):
        self.max_file_size = max_file_size
        if widget_index_exists():
            self.file = get_widget_by_index()
            self.file.description = label
        else:
            self.file = ipywidgets.FileUpload(
                description=label
            )
            self.file.filepath = None
            add_widget(self.file.model_id, self.file)
        display(self)


    @property
    def value(self):
        if len(self.file.value):
            return self.file.value[0].content
        return None

    @property 
    def filename(self):
        if len(self.file.value):
            return self.file.value[0].name
        return None 

    @property
    def filepath(self):
        if not len(self.file.value):
            return None
        if self.file.filepath is None:
            # store file in temp dir
            # and return the path
            temp_dir = tempfile.TemporaryDirectory()
            self.file.filepath = os.path.join(temp_dir.name, self.filename)

            with open(self.file.filepath, "wb") as fout:
                fout.write(self.value)
            
            return self.file.filepath
        
        return self.file.filepath

    @value.setter
    def value(self, v):
        print("file setter")

        tu = TemporaryUpload.objects.get(upload_id=v)
        self.file.filepath = tu.get_file_path()
        self.file.value = ({
            "name": tu.upload_name,
            "content": None,
        },)

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
