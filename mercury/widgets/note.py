import json

import ipywidgets
from IPython.display import Markdown, display

from .manager import WidgetException, WidgetsManager


class NoteText:
    def __init__(self, text):
        self.value = text


class Note:
    """
    The Note class provides an interface for adding Markdown-formatted notes within 
    the Mercury UI sidebar.
    
    This class supports Markdown, a lightweight and easy-to-use syntax for styling 
    all forms of writing on the Mercury platform. Users can add notes with emphasis, 
    lists, links, and more using the standard Markdown syntax.

    Parameters
    ----------
    text : str, default '*Note*'
        The Markdown-formatted text to be displayed in the Mercury UI sidebar. 
        If an empty string is provided, the note will display no text.

    Attributes
    ----------
    value : str
        The current Markdown text of the note. This can be set or retrieved at any time.

    Examples
    --------
    Adding a new Markdown note to the Mercury sidebar.
    >>> import mercury as mr
    >>> my_note = mr.Note(text="Some **Markdown** text")

    The note with the text "Some **Markdown** text" (with "Markdown" bolded) is now 
    displayed in the sidebar.
    """

    def __init__(self, text="*Note*"):
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
