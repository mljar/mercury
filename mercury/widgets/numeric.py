import json

import ipywidgets
from IPython.display import display

from .manager import (
    WidgetException,
    add_widget,
    get_widget,
    get_widget_by_index,
    widget_index_exists,
)


class Numeric:
    def __init__(self, value=0, min=0, max=10, label="", step=1):
        if value < min:
            raise WidgetException("value should be equal or larger than min")
        if value > max:
            raise WidgetException("value should be equal or smaller than max")

        if widget_index_exists():
            self.numeric = get_widget_by_index()
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
        else:
            self.numeric = ipywidgets.BoundedFloatText(
                value=value,
                min=min,
                max=max,
                description=label,
                step=step,
            )
            add_widget(self.numeric.model_id, self.numeric)
        display(self)

    @property
    def value(self):
        return self.numeric.value

    #@value.setter
    #def value(self, v):
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
            }
            data["application/mercury+json"] = json.dumps(view, indent=4)
            if "text/plain" in data:
                del data["text/plain"]

            return data
