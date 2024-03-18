import json

import ipywidgets
from IPython.display import display

from .manager import WidgetException, WidgetsManager


class Text:
    """
    The Text class introduces a text widget in the Mercury UI sidebar.
    This widget can function as a text field when `rows=1` or as a text area 
    when `rows` is greater than one.

    By using this widget, users can input text data into Mercury applications 
    dynamically. Once created, the value of the text can be accessed programmatically.

    Parameters
    ----------
    value : str, default ''
        The initial content of the text widget. Defaults to an empty string.

    label : str, default 'Text'
        The label that will appear alongside the text widget in the UI. 
        If an empty string is provided, it will display no text.

    rows : int, default 1
        Determines the height of the text widget:
        - When `rows=1`, the widget behaves as a single-line text field.
        - When `rows` is greater than one, the widget behaves as a multi-line text area.

    url_key : str, default ''
        If set, this allows the widget's value to be influenced by URL parameters, 
        facilitating the sharing of the widget's state via the URL. Defaults to an 
        empty string.

    disabled : bool, default False
        If set to True, the text widget will be displayed in the UI but will be inactive, 
        preventing user interactions. Defaults to False.

    hidden : bool, default False
        If set to True, the widget will not be visible in the UI. Defaults to False.
    
    sanitize : bool, default True
        If set to True, the string value will be sanitized, for example characters like
        quotes or parentheses will be removed.
    
        
    Attributes
    ----------
    value : str
        Retrieves the current content of the text widget.
    
    Examples
    --------
    Creating a Text widget:
    >>> import mercury as mr
    >>> name = mr.Text(value="Piotr", label="What is your name?", rows=1)
    >>> # Prints: "Hello Piotr!"
    >>> print(f"Hello {name.value}!")

    Creating a Text widget with a URL key allows its current value to be 
    reflected in the URL, facilitating the sharing of the widget's state with others:
    >>> name_url = mr.Text(value="Piotr", label="What is your name?", rows=1, url_key="name")
    >>> # If the text widget's content is "Piotr" and you click the 'Share' button in the 
    >>> # Mercury sidebar, it might produce a URL like: 
    >>> # https://your-server-address.com/app/notebook-name?name=Piotr
    >>> # The '?name=Piotr' at the end of the URL indicates that the text widget's 
    >>> # content is "Piotr".
    >>> print(f"Hello {name_url.value}!")
    """

    def __init__(
        self, value="text", label="", rows=1, url_key="", disabled=False, hidden=False, sanitize=True
    ):
        self.rows = rows

        self.code_uid = WidgetsManager.get_code_uid("Text", key=url_key)
        self.url_key = url_key
        self.hidden = hidden
        self.sanitize = sanitize
        if WidgetsManager.widget_exists(self.code_uid):
            self.text = WidgetsManager.get_widget(self.code_uid)
            self.text.description = label
            self.text.disabled = disabled
        else:
            self.text = ipywidgets.Textarea(
                value=value, description=label, disabled=disabled
            )
            WidgetsManager.add_widget(self.text.model_id, self.code_uid, self.text)
        display(self)

    @property
    def value(self):
        return self.text.value

    # @value.setter
    # def value(self, v):
    #    self.text.value = v

    def __str__(self):
        return "mercury.Text"

    def __repr__(self):
        return "mercury.Text"

    def _repr_mimebundle_(self, **kwargs):
        # data = {}
        # data["text/plain"] = repr(self)
        # return data
        data = self.text._repr_mimebundle_()

        if len(data) > 1:
            view = {
                "widget": "Text",
                "value": self.text.value,
                "sanitize": self.sanitize,
                "rows": self.rows,
                "label": self.text.description,
                "model_id": self.text.model_id,
                "code_uid": self.code_uid,
                "url_key": self.url_key,
                "disabled": self.text.disabled,
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
