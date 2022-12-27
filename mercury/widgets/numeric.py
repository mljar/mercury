import ipywidgets
import json

from IPython.display import display

from .manager import WidgetException, add_widget, get_widget, get_widget_by_index, widget_index_exists


class Numeric:
    def __init__(
        self, value=0, min_value=0, max_value=10, label="", step=1
    ):
        if value < min_value:
            raise WidgetException("value should be equal or larger than min_value")
        if value > max_value:
            raise WidgetException("value should be equal or smaller than max_value")

        if widget_index_exists():
            self.numeric = get_widget_by_index()
            if self.numeric.min != min_value:
                self.numeric.min = min_value
                self.numeric.value = value
            if self.numeric.max != max_value:
                self.numeric.max = max_value
                self.numeric.value = value
            if self.numeric.step != step:
                self.numeric.step = step
                self.numeric.value = value
            self.numeric.description = label
        else:
            self.numeric = ipywidgets.BoundedFloatText(
                value=value,
                min=min_value,
                max=max_value,
                description=label,
                step=step,
            )
            add_widget(self.numeric.model_id, self.numeric)
        display(self)

    @property
    def value(self):
        return self.numeric.value

    @value.setter
    def value(self, v):
        self.numeric.value = v

    def __str__(self):
        return "m.Numeric"

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
