import json

import ipywidgets
from IPython.display import display

from .manager import WidgetException, WidgetsManager


class Button:
    def __init__(self, label="", style="primary", disabled=False, hidden=False):
        self.code_uid = WidgetsManager.get_code_uid("Button")

        if style not in ["primary", "success", "info", "warning", "danger", ""]:
            style = "primary"
        self.hidden = hidden

        if WidgetsManager.widget_exists(self.code_uid):
            self.button = WidgetsManager.get_widget(self.code_uid)
            self.button.description = label
            self.button.button_style = style
            self.button.disabled = disabled
        else:
            self.button = ipywidgets.Button(
                description=label, button_style=style, disabled=disabled
            )
            self.button.value = False

            def on_button_clicked(b):
                self.button.value = True

            self.button.on_click(on_button_clicked)

            WidgetsManager.add_widget(self.button.model_id, self.code_uid, self.button)

        display(self)

    @property
    def clicked(self):
        if self.button.value:
            self.button.value = False
            return True
        return False

    def __str__(self):
        return "mercury.Button"

    def __repr__(self):
        return "mercury.Button"

    def _repr_mimebundle_(self, **kwargs):
        # data = {}
        # data["text/plain"] = repr(self)
        # return data
        data = self.button._repr_mimebundle_()

        if len(data) > 1:
            view = {
                "widget": "Button",
                "label": self.button.description,
                "style": self.button.button_style,
                "value": False,
                "model_id": self.button.model_id,
                "code_uid": self.code_uid,
                "disabled": self.button.disabled,
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
