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
    def __init__(
        self,
        value=0,
        min=0,
        max=10,
        label="",
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
