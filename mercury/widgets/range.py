import json

import ipywidgets
from IPython.display import display

from .manager import WidgetException, WidgetsManager
from .slider import get_number_format


class Range:
    """
    The Range class provides a double-slider widget in the Mercury UI sidebar, 
    enabling users to select a numeric range.

    The widget can be used to capture a range of numeric inputs and provides 
    an interactive and visual way to select ranges.

    Parameters
    ----------
    value : list of two ints or floats, default [0, 1]
        Initial values of the range widget, specifying the lower and upper bounds.

    min : int or float, default 0
        The minimum allowed value for the range slider.

    max : int or float, default 10
        The maximum allowed value for the range slider.

    label : str, default 'Range'
        Label that will be displayed alongside the range widget in the UI.
        If an empty string is provided, it will display no text.

    step : int or float, default 1
        Incremental step value for the slider movement.

    url_key : str, default ''
        If set, enables the widget's value to be influenced by URL parameters, 
        thus facilitating the sharing of the widget's state via the URL.

    disabled : bool, default False
        If True, the range widget will be displayed in the UI but will be inactive, 
        preventing user interactions.

    hidden : bool, default False
        If True, the widget will not be visible in the UI.
    
    Attributes
    ----------
    value : list of two ints or floats
        Retrieves the current range selected by the user in the widget.

    Examples
    --------
    Initializing a Range widget:
    >>> import mercury as mr
    >>> my_range = mr.Range(value=[1, 6], min=0, max=10, label="Select a range", step=1)
    >>> print(f"Selected range: {my_range.value[0]} to {my_range.value[1]}")

    Using a URL key allows for the widget's current range to be reflected in the URL, 
    enabling sharing of the widget's state:
    >>> my_range_url = mr.Range(value=[2, 7], min=0, max=10, label="Select a range", 
    >>>                         step=1, url_key="range")
    >>> # After selection, and clicking 'Share' in the Mercury sidebar, the URL might be: 
    >>> # https://your-server-address.com/app/notebook?range=3,5
    >>> # The '?range=3,5' at the end of the URL indicates that the range widget's
    >>> # content is a list of integer 3 and 5.
    >>> print(f"Your range starts at {my_range_url.value[0]} ends at {my_range_url.value[1]}")
    """

    def __init__(
        self,
        value=[0, 1],
        min=0,
        max=10,
        label="Range",
        step=1,
        url_key="",
        disabled=False,
        hidden=False,
    ):
        for i in [0, 1]:
            if value[i] < min:
                raise WidgetException(f"value[{i}] should be equal or larger than min")
            if value[i] > max:
                raise WidgetException(f"value[{i}] should be equal or smaller than max")

        if len(value) != 2:
            raise WidgetException("Range accepts list with length 2 as value")

        self.code_uid = WidgetsManager.get_code_uid("Range", key=url_key)
        self.url_key = url_key
        self.hidden = hidden
        if WidgetsManager.widget_exists(self.code_uid):
            self.range = WidgetsManager.get_widget(self.code_uid)
            if self.range.min != min:
                self.range.min = min
                self.range.value = value
            if self.range.max != max:
                self.range.max = max
                self.range.value = value
            if self.range.step != step:
                self.range.step = step
                self.range.value = value
            self.range.description = label
            self.range.disabled = disabled
        else:
            RangeConstructor = ipywidgets.IntRangeSlider
            number_format = "d"
            if isinstance(step, float):
                RangeConstructor = ipywidgets.FloatRangeSlider
                number_format = get_number_format(step)

            self.range = RangeConstructor(
                value=value,
                min=min,
                max=max,
                description=label,
                step=step,
                style={"description_width": "initial"},
                disabled=disabled,
                readout_format=number_format,
            )
            WidgetsManager.add_widget(self.range.model_id, self.code_uid, self.range)
        display(self)

    @property
    def value(self):
        return list(self.range.value)

    def __str__(self):
        return "mercury.Range"

    def __repr__(self):
        return "mercury.Range"

    def _repr_mimebundle_(self, **kwargs):
        # data = {}
        # data["text/plain"] = repr(self)
        # return data
        data = self.range._repr_mimebundle_()

        if len(data) > 1:
            view = {
                "widget": "Range",
                "value": self.range.value,
                "min": self.range.min,
                "max": self.range.max,
                "step": self.range.step,
                "label": self.range.description,
                "model_id": self.range.model_id,
                "code_uid": self.code_uid,
                "url_key": self.url_key,
                "disabled": self.range.disabled,
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
