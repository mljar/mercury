import json

import ipywidgets
from IPython.display import display

from .manager import WidgetException, WidgetsManager


class Slider:
    def __init__(self, value=0, min=0, max=10, label="", step=1):
        if value < min:
            raise WidgetException("value should be equal or larger than min")
        if value > max:
            raise WidgetException("value should be equal or smaller than max")

        self.code_uid = WidgetsManager.get_code_uid("Slider")

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
        else:
            self.slider = ipywidgets.IntSlider(
                value=value,
                min=min,
                max=max,
                description=label,
                step=step,
                style={"description_width": "initial"},
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
            }
            data["application/mercury+json"] = json.dumps(view, indent=4)
            if "text/plain" in data:
                del data["text/plain"]

            return data
