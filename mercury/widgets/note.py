import json

import ipywidgets
from IPython.display import Markdown, display

from .manager import WidgetException, WidgetsManager


class NoteText:
    def __init__(self, text):
        self.value = text


class Note:
    def __init__(self, text=""):

        self.code_uid = WidgetsManager.get_code_uid("Note")

        if WidgetsManager.widget_exists(self.code_uid):
            self.note = WidgetsManager.get_widget(self.code_uid)
            if self.note.value != text:
                self.note.value = text
        else:
            self.note = NoteText(text)
            WidgetsManager.add_widget(self.code_uid, self.code_uid, self.note)
        display(self)

    @property
    def value(self):
        return self.note.value

    def __str__(self):
        return "mercury.Note"

    def __repr__(self):
        return "mercury.Note"

    def _repr_mimebundle_(self, **kwargs):

        data = {}

        view = {
            "widget": "Note",
            "value": self.note.value,
            "model_id": self.code_uid,
            "code_uid": self.code_uid,
        }
        data["application/mercury+json"] = json.dumps(view, indent=4)

        data["text/markdown"] = self.note.value

        return data
