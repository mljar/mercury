import ipywidgets
import json

from IPython.display import display


mercury_widgets = {}
updates_list = []

def add_widget(model_id, widget):
    mercury_widgets[model_id] = widget

def get_widget(model_id):
    return mercury_widgets.get(model_id, None)

def get_update(model_id, field):
    w = get_widget(model_id)
    if w is None:
        return None    
    return getattr(w, field)

def set_update(model_id, field, new_value):
    w = get_widget(model_id)
    if w is not None:
        setattr(w, field, new_value)

class Slider:

    def __init__(self, value = 0, min_value=0, max_value=10, label="", step=1, model_id=""):
        if model_id != "":
            self = get_widget(model_id)
        else:
            self.slider = ipywidgets.IntSlider(
                value = value,
                min=min_value,
                max=max_value,
                description=label,
                step=step,
            )
            add_widget(self.slider.model_id, self)
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
            "model_id": self.slider.model_id,
        }
        return "mercury.Slider " + json.dumps(data, indent=4)
    
    def _repr_mimebundle_(self, **kwargs):
        #data = {}
        #data["text/plain"] = repr(self)
        #return data
        data = self.slider._repr_mimebundle_()
        if len(data) > 1:
            data["text/plain"] = repr(self)
            return data


