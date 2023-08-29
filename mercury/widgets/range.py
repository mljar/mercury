import json

import ipywidgets
from IPython.display import display

from .manager import WidgetException, WidgetsManager
from .slider import get_number_format


class Range:
    def __init__(
        self,
        value=[0, 1],
        min=0,
        max=10,
        label="",
        step=1,
        url_key="",
        disabled=False,
        hidden=False,
    ):
        for i in [0, 1]:
            if value[i] < min:
                raise WidgetException(f"value[{i}] should be equal or larger than min")
            if value[i] > max:
                raise WidgetException(f"value[{i}] should be equal or smaller than max")

        if len(value) != 2:
            raise WidgetException("Range accepts list with length 2 as value")

        self.code_uid = WidgetsManager.get_code_uid("Range", key=url_key)
        self.url_key = url_key
        self.hidden = hidden
        if WidgetsManager.widget_exists(self.code_uid):
            self.range = WidgetsManager.get_widget(self.code_uid)
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
            self.range.disabled = disabled
        else:
            RangeConstructor = ipywidgets.IntRangeSlider
            number_format = "d"
            if isinstance(step, float):
                RangeConstructor = ipywidgets.FloatRangeSlider
                number_format = get_number_format(step)

            self.range = RangeConstructor(
                value=value,
                min=min,
                max=max,
                description=label,
                step=step,
                style={"description_width": "initial"},
                disabled=disabled,
                readout_format=number_format,
            )
            WidgetsManager.add_widget(self.range.model_id, self.code_uid, self.range)
        display(self)

    @property
    def value(self):
        return list(self.range.value)

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
                "code_uid": self.code_uid,
                "url_key": self.url_key,
                "disabled": self.range.disabled,
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
