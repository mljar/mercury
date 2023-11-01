import json

import ipywidgets
from IPython.display import display

from .manager import WidgetException, WidgetsManager


def get_number_format(step):
    number_format = ".2f"
    if "." in str(step):
        try:
            number_format = f".{len(str(step).split('.')[1])}f"
        except Exception as e:
            pass
    return number_format


class Slider:
    """
    The Slider class introduces a slider widget in the Mercury UI sidebar, 
    enabling users to select a value by sliding along a range.

    This widget provides a dynamic way for users to set a numeric value within 
    a defined range. The current value of the slider can be accessed 
    programmatically, facilitating dynamic responses to user input within Mercury 
    applications.

    Parameters
    ----------
    value : int or float, default 0
        The initial value of the slider. Should be between `min` and `max`. 
        Defaults to 0.

    min : int or float, default 0
        The minimum allowed value for the slider. Defaults to 0.

    max : int or float, default 10
        The maximum allowed value for the slider. Defaults to 10.

    label : str, default 'Slider'
        The label that will appear alongside the slider widget in the UI. 
        If an empty string is provided, it will display no text.

    step : int or float, default 1
        The granularity of the slider. This determines the smallest possible change 
        in value when sliding.

    url_key : str, default ''
        If set, this allows the widget's value to be influenced by URL parameters, 
        facilitating the sharing of the widget's state via the URL. Defaults to an 
        empty string.

    disabled : bool, default False
        If set to True, the slider will be displayed in the UI but will be inactive, 
        preventing user interactions. Defaults to False.

    hidden : bool, default False
        If set to True, the widget will not be visible in the UI. Defaults to False.
    
    Attributes
    ----------
    value : int or float
        Retrieves the current value set by the slider.
    
    Examples
    --------
    Creating a Slider widget:
    >>> import mercury as mr
    >>> your_slider = mr.Slider(value=5, 
    ...                         min=0, 
    ...                         max=10, 
    ...                         label="Your favourite number", 
    ...                         step=1)
    >>> # Prints: "Your value is 5"
    >>> print(f"Your value is {your_slider.value}")

    Creating a Slider widget with a URL key allows its current value to be 
    reflected in the URL, which is useful for sharing the current state of the 
    application with others through a URL:
    >>> your_slider_url = mr.Slider(value=0, 
    ...                             min=0, 
    ...                             max=10, 
    ...                             label="Your favourite number", 
    ...                             step=1, 
    ...                             url_key="slider")
    >>> # If the slider is set to 3 and you click the 'Share' button in the Mercury 
    >>> # sidebar, it might produce a URL like: 
    >>> # https://your-server-address.com/app/notebook-name?slider=3
    >>> # The '?slider=3' at the end of the URL indicates that the slider is set to 3.
    >>> print(f"Your value is {your_slider_url.value}")
    """

    def __init__(
        self,
        value=0,
        min=0,
        max=10,
        label="Slider",
        step=1,
        url_key="",
        disabled=False,
        hidden=False,
    ):
        if value < min:
            raise WidgetException("value should be equal or larger than min")
        if value > max:
            raise WidgetException("value should be equal or smaller than max")

        self.code_uid = WidgetsManager.get_code_uid("Slider", key=url_key)
        self.url_key = url_key
        self.hidden = hidden
        if WidgetsManager.widget_exists(self.code_uid):
            self.slider = WidgetsManager.get_widget(self.code_uid)
            if self.slider.min != min:
                self.slider.min = min
                self.slider.value = value
            if self.slider.max != max:
                self.slider.max = max
                self.slider.value = value
            if self.slider.step != step:
                self.slider.step = step
                self.slider.value = value
            self.slider.description = label
            self.slider.disabled = disabled
        else:
            SliderConstructor = ipywidgets.IntSlider
            number_format = "d"
            if isinstance(step, float):
                SliderConstructor = ipywidgets.FloatSlider
                number_format = get_number_format(step)

            self.slider = SliderConstructor(
                value=value,
                min=min,
                max=max,
                description=label,
                step=step,
                style={"description_width": "initial"},
                disabled=disabled,
                readout_format=number_format,
            )
            WidgetsManager.add_widget(self.slider.model_id, self.code_uid, self.slider)
        display(self)

    @property
    def value(self):
        return self.slider.value

    # @value.setter
    # def value(self, v):
    #    self.slider.value = v

    def __str__(self):
        return "mercury.Slider"

    def __repr__(self):
        return "mercury.Slider"

    def _repr_mimebundle_(self, **kwargs):
        # data = {}
        # data["text/plain"] = repr(self)
        # return data
        data = self.slider._repr_mimebundle_()

        if len(data) > 1:
            view = {
                "widget": "Slider",
                "value": self.slider.value,
                "min": self.slider.min,
                "max": self.slider.max,
                "step": self.slider.step,
                "label": self.slider.description,
                "model_id": self.slider.model_id,
                "code_uid": self.code_uid,
                "url_key": self.url_key,
                "disabled": self.slider.disabled,
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
