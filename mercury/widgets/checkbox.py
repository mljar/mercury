import json

import ipywidgets
from IPython.display import display

from .manager import WidgetsManager


class Checkbox:
    """
    The Checkbox class creates an interactive checkbox widget manifested as a 
    toggle switch in the Mercury UI sidebar.

    This widget allows users to toggle a selection (i.e., checked or unchecked) in 
    the UI, which can then be used to control the logic in the application. This class 
    also supports synchronizing the state of the checkbox with URL parameters for 
    easy sharing.

    Parameters
    ----------
    value : bool, default True
        The initial state of the checkbox. If True, the checkbox is checked; if False, 
        it's unchecked.

    label : str, default 'Checkbox'
        The text label displayed alongside the checkbox. If an empty string 
        is provided, the checkbox will display no text.

    url_key : str, default ''
        If provided, this allows the checkbox's state to be synchronized with a URL 
        parameter. The state of the checkbox can then be set and shared via the URL.

    disabled : bool, default False
        If True, the checkbox is rendered inactive in the UI and cannot be interacted 
        with.

    hidden : bool, default False
        If True, the checkbox is not visible in the sidebar. The default is False, 
        meaning the checkbox is visible.

    Attributes
    ----------
    value : bool
        A property that can be set or retrieved to change or get the checkbox's 
        current state.

    Examples
    --------
    Creating a Checkbox with a label, and checking its state.
    >>> import mercury as mr
    >>> my_flag = mr.Checkbox(value=True, label="Switch me")
    >>> if my_flag.value:
    >>>     print("Checkbox is ON")
    >>> else:
    >>>     print("Checkbox is OFF")

    Creating a Checkbox with a URL key, which allows its state to be shared via 
    the URL. This feature is useful for sharing the current state of the application 
    with others by just sharing the URL.
    >>> my_flag = mr.Checkbox(value=True, label="Switch me", url_key="flag")
    >>> # The state of the checkbox can now be reflected in the URL.
    >>> # For instance, if the checkbox is checked, and you click the 'Share' button 
    >>> # in the Mercury sidebar, it will generate a URL like: 
    >>> # https://your-server-address.com/app/notebook-name?flag=true
    >>> # The '?flag=true' at the end of the URL indicates that the checkbox is checked.
    >>> print(my_flag.value)  # Prints: True
    """

    def __init__(self, value=True, label="Checkbox", url_key="", disabled=False, hidden=False):
        self.code_uid = WidgetsManager.get_code_uid("Checkbox", key=url_key)
        self.url_key = url_key
        self.hidden = hidden
        if WidgetsManager.widget_exists(self.code_uid):
            self.checkbox = WidgetsManager.get_widget(self.code_uid)
            self.checkbox.description = label
            self.checkbox.disabled = disabled
        else:
            self.checkbox = ipywidgets.Checkbox(
                value=value,
                description=label,
                style={"description_width": "initial"},
                disabled=disabled,
            )
            WidgetsManager.add_widget(
                self.checkbox.model_id, self.code_uid, self.checkbox
            )
        display(self)

    @property
    def value(self):
        return self.checkbox.value

    @value.setter
    def value(self, v):
        self.checkbox.value = v

    def __str__(self):
        return "mercury.Checkbox"

    def __repr__(self):
        return "mercury.Checkbox"

    def _repr_mimebundle_(self, **kwargs):
        # data = {}
        # data["text/plain"] = repr(self)
        # return data
        data = self.checkbox._repr_mimebundle_()

        if len(data) > 1:
            view = {
                "widget": "Checkbox",
                "value": self.checkbox.value,
                "label": self.checkbox.description,
                "model_id": self.checkbox.model_id,
                "code_uid": self.code_uid,
                "url_key": self.url_key,
                "disabled": self.checkbox.disabled,
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
