import ipywidgets
import json

from IPython.display import display

from .manager import add_widget, get_widget, get_widget_by_index, widget_index_exists


class Select:
    def __init__(
        self, value=0, choices=[], label="", multi=False
    ):
        self.multi = multi
        if widget_index_exists():
            self.dropdown = get_widget_by_index()
        else:
            self.dropdown = ipywidgets.Dropdown(
                value=value,
                options=choices,
                description=label,
            )
            add_widget(self.slider.model_id, self.dropdown)
        display(self)

    @property
    def value(self):
        return self.slider.value

    @value.setter
    def value(self, v):
        self.slider.value = v


    @property 
    def choices(self):
        return self.dropdown.choices

    @choices.setter
    def choices(self, new_choices):
        self.dropdown.choices = new_choices

    def __str__(self):
        return "m.Select"

    def __repr__(self):

        return "mercury.Select"

    def _repr_mimebundle_(self, **kwargs):
        # data = {}
        # data["text/plain"] = repr(self)
        # return data
        data = self.slider._repr_mimebundle_()
        
        if len(data) > 1:
            view = {
                "widget": "Select",
                "value": self.dropdown.value,
                "choices": self.dropdown.options,
                "multi": self.multi,
                "label": self.dropdown.description,
                "model_id": self.dropdown.model_id,
            }
            data["application/mercury+json"] = json.dumps(view, indent=4)
            if "text/plain" in data:
                del data["text/plain"]
                
            return data
