import ipywidgets
import json

from IPython.display import display

from .manager import add_widget, get_widget, get_widget_by_index, widget_index_exists


class Slider:
    def __init__(
        self, value=0, min_value=0, max_value=10, label="", step=1, model_id=""
    ):
        if widget_index_exists():
            self.slider = get_widget_by_index()
        else:
            self.slider = ipywidgets.IntSlider(
                value=value,
                min=min_value,
                max=max_value,
                description=label,
                step=step,
            )
            add_widget(self.slider.model_id, self.slider)
        display(self)

    @property
    def value(self):
        return self.slider.value

    @value.setter
    def value(self, v):
        self.slider.value = v

    def __str__(self):
        return "m.Slider"

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
            }
            data["application/mercury+json"] = json.dumps(view, indent=4)
            if "text/plain" in data:
                del data["text/plain"]
                
            return data
