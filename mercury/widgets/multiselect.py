import json

import ipywidgets
from IPython.display import display

from .manager import WidgetsManager


class MultiSelect:
    """
    The MultiSelect class introduces a multi-selection widget in the Mercury UI sidebar, 
    allowing users to interactively choose multiple options from a predefined list.

    Displayed as a dropdown menu, this widget permits users to select 
    multiple choices from a given collection. Each choice is defined as a 
    string, and the entire set of options is customizable. The selected values 
    can be accessed programmatically, catering for dynamic reactions to user 
    input within Mercury applications.

    Parameters
    ----------
    value : list of str, default []
        The initial selection(s) in the list. If not provided and the choices list 
        is non-empty, defaults to the first item in the choices list. Defaults to 
        an empty list.

    choices : list of str, default []
        The list of available options for users to select from. Defaults to an 
        empty list.

    label : str, default 'MultiSelect'
        The label displayed next to the multi-selection widget. If an empty string 
        is provided, it will display no text.

    url_key : str, default ''
        When set, this allows the widget's selections to be influenced by URL parameters, 
        enabling the sharing of the widget's state via the URL. Defaults to an 
        empty string.

    disabled : bool, default False
        If True, the list is displayed in the UI but is inactive, 
        preventing user interactions. Defaults to False.

    hidden : bool, default False
        If set to True, the widget will not be displayed in the UI. Defaults to False.
    
    Attributes
    ----------
    value : list of str
        Retrieves the currently selected values from the list.
    
    Examples
    --------
    Creating a MultiSelect widget with a set of options.
    >>> import mercury as mr
    >>> my_selections = mr.MultiSelect(value=["Option2"],
    ...                                choices=["Option1", "Option2", "Option3"], 
    ...                                label="Select options")
    >>> # Prints: "Current selections: ['Option2']"
    >>> print(f"Current selections: {my_selections.value}")
    
    The first item in the `choices` list will be selected by default if `value` 
    is not specified. The current selections can be obtained programmatically, 
    useful for tailoring application behavior based on user choices.

    Creating a MultiSelect widget with a URL key facilitates the current selections 
    to be captured in the URL. This feature is especially useful for sharing the 
    present state of the application with others through a URL.
    >>> my_options = mr.MultiSelect(value=["Option2"], 
    ...                             choices=["Option1", "Option2", "Option3"], 
    ...                             label="Pick options", 
    ...                             url_key="options")
    >>> # If "Option2" and "Option3" are selected and you hit the 'Share' button 
    >>> # in the Mercury sidebar, a URL similar to this might be produced: 
    >>> # https://your-server-address.com/app/notebook-name?options=Option2,Option3
    >>> # The '?options=Option2,Option3' at the end indicates that both "Option2" 
    >>> # and "Option3" are selected.
    >>> # Prints: "['Option1']" if no values are set in the URL, or the 
    >>> # corresponding options reflected in the "options" URL parameter.
    >>> print(my_options.value)
    """

    def __init__(
        self, value=[], choices=[], label="MultiSelect", url_key="", disabled=False, hidden=False
    ):
        if not value and len(choices) > 1:
            value = [choices[0]]

        self.code_uid = WidgetsManager.get_code_uid("MultiSelect", key=url_key)
        self.url_key = url_key
        self.hidden = hidden
        choices = [i for i in list(choices) if isinstance(i, str)]
        value = [i for i in list(value) if isinstance(i, str)]
        
        if WidgetsManager.widget_exists(self.code_uid):
            self.select = WidgetsManager.get_widget(self.code_uid)
            if list(self.select.options) != choices:
                self.select.options = choices
                self.select.value = value
            self.select.description = label
            self.select.disabled = disabled
        else:
            self.select = ipywidgets.SelectMultiple(
                value=value,
                options=choices,
                description=label,
                style={"description_width": "initial"},
                disabled=disabled,
            )
            WidgetsManager.add_widget(self.select.model_id, self.code_uid, self.select)
        display(self)

    @property
    def value(self):
        return list(self.select.value)

    @value.setter
    def value(self, v):
        try:
            self.select.value = v
        except Exception as e:
            if len(self.select.options) > 0:
                self.select.value = self.select.options[0]
            else:
                self.select.value = None

    def __str__(self):
        return "m.MultiSelect"

    def __repr__(self):
        return "mercury.MultiSelect"

    def _repr_mimebundle_(self, **kwargs):
        # data = {}
        # data["text/plain"] = repr(self)
        # return data
        data = self.select._repr_mimebundle_()

        if len(data) > 1:
            view = {
                "widget": "MultiSelect",
                "value": self.select.value,
                "choices": self.select.options,
                "label": self.select.description,
                "model_id": self.select.model_id,
                "code_uid": self.code_uid,
                "url_key": self.url_key,
                "disabled": self.select.disabled,
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
