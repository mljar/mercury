import json

import ipywidgets
from IPython.display import display

from .manager import WidgetException, WidgetsManager


class Numeric:
    """
    The Numeric class creates a widget for numerical input within the Mercury UI 
    sidebar. It allows for interactive user input, specifically for numerical 
    values within a defined range.
    
    The widget is displayed as a bounded input box with increment and decrement 
    buttons, allowing for increases or decreases by a specific step size. The value 
    is restricted within a minimum and maximum range.

    Parameters
    ----------
    value : float, default 0
        The initial value of the widget. Must be within the range defined by the 
        `min` and `max` parameters. Defaults to 0.
    
    min : float, default 0
        The minimum allowable value for the widget. Defaults to 0.
    
    max : float, default 10
        The maximum allowable value for the widget. Defaults to 10.
    
    label : str, default 'Numeric'
        The description label displayed alongside the widget. If an empty string 
        is provided, the numeric will display no text.
    
    step : float, default 1
        The increment value for each step, determining how much the value changes 
        each time the user interacts with the increment and decrement buttons. 
        Defaults to 1.
    
    url_key : str, default ''
        When set, allows the widget's value to be influenced by URL parameters. 
        Defaults to an empty string.
    
    disabled : bool, default False
        If True, the widget is rendered inactive in the UI, preventing user 
        interaction. Defaults to False.
    
    hidden : bool, default False
        If True, the widget is not visible in the UI. Defaults to False.

    Attributes
    ----------
    value : float
        The current value of the widget. This can be set or retrieved at any time.

    Examples
    --------
    Creating a Numeric widget in the Mercury sidebar.
    >>> import mercury as mr
    >>> my_number = mr.Numeric(value=0,
    ...                        min=0,
    ...                        max=10,
    ...                        label="Your favourite number",
    ...                        step=1)
    >>> print(f"Value is {my_number.value}")  # Prints: Value is 0

    Creating a Numeric widget with a URL key, which allows its current value to 
    be shared via the URL. This feature is useful for sharing the current state 
    of the application with others by just sharing the URL.
    >>> my_number = mr.Numeric(value=5, 
    ...                    min=0, 
    ...                    max=10, 
    ...                    label="Set a number", 
    ...                    step=1, 
    ...                    url_key="number")
    >>> # The value of the Numeric widget can now be reflected in the URL.
    >>> # For instance, if you set the number to 5 and click the 'Share' button 
    >>> # in the Mercury sidebar, it will generate a URL like: 
    >>> # https://your-server-address.com/app/notebook-name?number=5
    >>> # The '?number=5' at the end of the URL indicates that the numeric 
    >>> # input is set to 5.
    >>> print(my_number.value)  # Prints: 5
    """

    def __init__(
        self,
        value=0,
        min=0,
        max=10,
        label="Numeric",
        step=1,
        url_key="",
        disabled=False,
        hidden=False,
    ):
        if value < min:
            raise WidgetException("value should be equal or larger than min")
        if value > max:
            raise WidgetException("value should be equal or smaller than max")

        self.code_uid = WidgetsManager.get_code_uid("Numeric", key=url_key)
        self.url_key = url_key
        self.hidden = hidden
        if WidgetsManager.widget_exists(self.code_uid):
            self.numeric = WidgetsManager.get_widget(self.code_uid)
            if self.numeric.min != min:
                self.numeric.min = min
                self.numeric.value = value
            if self.numeric.max != max:
                self.numeric.max = max
                self.numeric.value = value
            if self.numeric.step != step:
                self.numeric.step = step
                self.numeric.value = value
            self.numeric.description = label
            self.numeric.disabled = disabled
        else:
            self.numeric = ipywidgets.BoundedFloatText(
                value=value,
                min=min,
                max=max,
                description=label,
                step=step,
                style={"description_width": "initial"},
                disabled=disabled,
            )
            WidgetsManager.add_widget(
                self.numeric.model_id, self.code_uid, self.numeric
            )
        display(self)

    @property
    def value(self):
        return self.numeric.value

    # @value.setter
    # def value(self, v):
    #    self.numeric.value = v

    def __str__(self):
        return "mercury.Numeric"

    def __repr__(self):
        return "mercury.Numeric"

    def _repr_mimebundle_(self, **kwargs):
        # data = {}
        # data["text/plain"] = repr(self)
        # return data
        data = self.numeric._repr_mimebundle_()

        if len(data) > 1:
            view = {
                "widget": "Numeric",
                "value": self.numeric.value,
                "min": self.numeric.min,
                "max": self.numeric.max,
                "step": self.numeric.step,
                "label": self.numeric.description,
                "model_id": self.numeric.model_id,
                "code_uid": self.code_uid,
                "url_key": self.url_key,
                "disabled": self.numeric.disabled,
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
