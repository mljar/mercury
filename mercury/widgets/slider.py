import ipywidgets
import json

from IPython.display import display


class Slider:

    def __init__(self, value = 0, min_value=0, max_value=10, label="", step=1):
        self.slider = ipywidgets.IntSlider(
            value = value,
            min=min_value,
            max=max_value,
            description=label,
            step=step,
        )
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
        data = {
            "value": self.slider.value,
            "min": self.slider.min,
            "max": self.slider.max,
            "step": self.slider.step,
            "label": self.slider.description,
        }
        return "mercury.Slider " + json.dumps(data, indent=4)
    
    def _repr_mimebundle_(self, **kwargs):
        data = self.slider._repr_mimebundle_()
        if len(data) > 1:
            data["text/plain"] = repr(self)
            return data


