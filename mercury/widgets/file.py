import json
import os
import tempfile
import atexit
import shutil

import ipywidgets
from IPython.display import display

from .manager import WidgetsManager


class File:
    """
    The File class provides an interface for uploading and reading files within 
    the Mercury UI sidebar.
    
    Files can be accessed as binary objects or read from a temporary file path. 
    The File class allows for file interactions such as uploading, retrieving the 
    file name, and reading file content in binary format or from the file path.

    Parameters
    ----------
    label : str, default 'File upload'
        The label of the file upload widget displayed in the UI. If an empty string 
        is provided, it will display no text.

    max_file_size : str, default '100MB'
        Specifies the maximum file size allowed for upload. The size should be a 
        string representing the limit in bytes, KB, MB, or GB (e.g., '100MB', '1GB').

    disabled : bool, default False
        Determines whether the file upload widget is disabled. If True, the widget 
        is displayed but cannot be interacted with.

    hidden : bool, default False
        Controls the visibility of the file upload widget in the sidebar. If True, 
        the widget will not be visible.

    Attributes
    ----------
    value : bytes
        The content of the uploaded file in binary format. If no file is uploaded, 
        returns None.

    filename : str
        The name of the uploaded file. If no file is uploaded, returns None.

    filepath : str
        The path to the temporary file stored on the server. If no file is uploaded, 
        returns None.

    Examples
    --------
    Uploading a file and reading its content.
    >>> import mercury as mr
    >>> my_file = mr.File(label="File upload", max_file_size="100MB")
    >>> # Only if a file is uploaded using the Mercury UI
    >>> if my_file.filepath:
    >>>     print(f"Uploaded file path: {my_file.filepath}")
    >>>     with open(my_file.filepath, "r") as fin:
    >>>         print(fin.read())
    >>>     print(f"Thanks for uploading {my_file.filename}")

    Retrieving file content in binary format.
    >>> # 'binary_content' is a bytes object containing the file data
    >>> binary_content = my_file.value
    """

    def __init__(
        self, label="File upload", max_file_size="100MB", disabled=False, hidden=False
    ):
        self.max_file_size = max_file_size
        self.code_uid = WidgetsManager.get_code_uid("File")
        self.temp_dir = None
        atexit.register(self.cleanup)
        self.hidden = hidden

        if WidgetsManager.widget_exists(self.code_uid):
            self.file = WidgetsManager.get_widget(self.code_uid)
            self.file.description = label
            self.file.disabled = disabled
        else:
            self.file = ipywidgets.FileUpload(description=label, disabled=disabled)
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
            with open(self.file.filepath, "rb") as fin:
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
            self.temp_dir = tempfile.mkdtemp()
            self.file.filepath = os.path.join(self.temp_dir, self.filename)

            with open(self.file.filepath, "wb") as fout:
                fout.write(self.value)

            return self.file.filepath

        return None

    def cleanup(self):
        if self.temp_dir is not None and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

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
                "disabled": self.file.disabled,
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
