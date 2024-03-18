import json

import ipywidgets
from IPython.display import display

from .manager import WidgetsManager

import warnings


class Select:
    """
    The Select class introduces a dropdown selection widget in the Mercury UI sidebar, 
    facilitating user interaction through the choosing of options from a predefined 
    list.

    Displayed as a standard dropdown menu, the widget allows users to choose a 
    single option from a collection of choices. Each choice is defined as a 
    string, and the entire set of options is customizable. The selected value can 
    be accessed programmatically, enabling dynamic responses to user input within 
    the Mercury applications.

    Parameters
    ----------
    value : str, default None
        The initial selection in the dropdown. If not provided, and the choices list 
        is non-empty, defaults to the first item in the choices list. Defaults to None.

    choices : list of str, default []
        The list of available options for the user to choose from in the dropdown. 
        Defaults to an empty list.

    label : str, default 'Select'
        The label displayed next to the dropdown widget. If an empty string 
        is provided, it will display no text.

    url_key : str, default ''
        When set, allows the widget's selection to be influenced by URL parameters, 
        facilitating the sharing of the widget's state via the URL. Defaults to an 
        empty string.

    disabled : bool, default False
        If set to True, the dropdown is displayed in the UI but is inactive, 
        preventing user interactions. Defaults to False.

    hidden : bool, default False
        If set to True, the widget will not be visible in the UI. Defaults to False.
    
    Attributes
    ----------
    value : str
        Retrieves the currently selected value from the dropdown.
    
    Examples
    --------
    Creating a Select widget with a set of options without `value` argument.
    >>> import mercury as mr
    >>> my_selection = mr.Select(choices=["Option1", "Option2", "Option3"], 
    ...                          label="Choose an option")
    >>> # Prints: "Current selection: Option1"
    >>> print(f"Current selection: {my_selection.value}")

    The first item in the `choices` list will be selected by default if `value` 
    is not specified. The current selection can be retrieved programmatically, 
    which is useful for adapting application behavior based on user input.

    Creating a Select widget with a set of options with `value` argument.
    >>> my_selection_with_default = mr.Select(value="Option2", 
    ...                                       choices=["Option1", "Option2", "Option3"], 
    ...                                       label="Choose an option")
    >>> # Prints: "Current selection: Option2"
    >>> print(f"Current selection: {my_selection_with_default.value}")

    Creating a Select widget with a URL key allows its current selection to be 
    reflected in the URL. This is particularly handy for sharing the current state 
    of the application with others via a simple URL.
    >>> my_option = mr.Select(choices=["Option1", "Option2", "Option3"], 
    ...                       label="Pick an option", 
    ...                       url_key="option")
    >>> # The current state of the selection can be reflected in the URL.
    >>> # For example, if "Option2" is selected and you click the 'Share' button 
    >>> # in the Mercury sidebar, it might generate a URL like: 
    >>> # https://your-server-address.com/app/notebook-name?option=Option2
    >>> # The '?option=Option2' at the end of the URL indicates that "Option2" is selected.
    >>> # Prints: "Option1" if no value is set in the URL, or the 
    >>> # corresponding option reflected in the "option" URL parameter.
    >>> print(my_option.value)
    """

    def __init__(
        self, value=None, choices=[], label="Select", url_key="", disabled=False, hidden=False
    ):
        if len(choices) == 0:
            raise Exception("Please provide choices list. God bless you <3")

        if value is None:
            value = choices[0]
        
        if value not in choices:
            value = choices[0]
            warnings.warn("\nYour value is not included in choices. Automatically set value to first element from choices.")


        self.code_uid = WidgetsManager.get_code_uid("Select", key=url_key)
        self.url_key = url_key
        self.hidden = hidden
        choices = [i for i in list(choices) if isinstance(i, str)]

        if WidgetsManager.widget_exists(self.code_uid):
            self.dropdown = WidgetsManager.get_widget(self.code_uid)
            if list(self.dropdown.options) != choices:
                self.dropdown.options = choices
                self.dropdown.value = value
            self.dropdown.description = label
            self.dropdown.disabled = disabled
        else:
            self.dropdown = ipywidgets.Dropdown(
                value=value,
                options=choices,
                description=label,
                style={"description_width": "initial"},
                disabled=disabled,
            )
            WidgetsManager.add_widget(
                self.dropdown.model_id, self.code_uid, self.dropdown
            )
        display(self)

    @property
    def value(self):
        return self.dropdown.value

    def __str__(self):
        return "m.Select"

    def __repr__(self):
        return "mercury.Select"

    def _repr_mimebundle_(self, **kwargs):
        # data = {}
        # data["text/plain"] = repr(self)
        # return data
        data = self.dropdown._repr_mimebundle_()

        if len(data) > 1:
            view = {
                "widget": "Select",
                "value": self.dropdown.value,
                "choices": self.dropdown.options,
                "label": self.dropdown.description,
                "model_id": self.dropdown.model_id,
                "code_uid": self.code_uid,
                "url_key": self.url_key,
                "disabled": self.dropdown.disabled,
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
