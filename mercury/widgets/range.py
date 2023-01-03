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


class Range:
    def __init__(self, value=[0, 1], min=0, max=10, label="", step=1):
        for i in [0, 1]:
            if value[i] < min:
                raise WidgetException(
                    f"value[{i}] should be equal or larger than min"
                )
            if value[i] > max:
                raise WidgetException(
                    f"value[{i}] should be equal or smaller than max"
                )

        if len(value) != 2:
            raise WidgetException("Range accepts list with length 2 as value")

        if widget_index_exists():
            self.range = get_widget_by_index()
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
        else:
            self.range = ipywidgets.IntRangeSlider(
                value=value,
                min=min,
                max=max,
                description=label,
                step=step,
            )
            add_widget(self.range.model_id, self.range)
        display(self)

    @property
    def value(self):
        return self.range.value

    #@value.setter
    #def value(self, v):
    #    self.range.value = v

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
            }
            data["application/mercury+json"] = json.dumps(view, indent=4)
            if "text/plain" in data:
                del data["text/plain"]

            return data
