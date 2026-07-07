# Copyright MLJAR Sp. z o.o.
# Licensed under the Apache License, Version 2.0 (Apache-2.0)

import warnings
from typing import Literal

import anywidget
import traitlets
from IPython.display import display

from .manager import MERCURY_MIMETYPE, WidgetsManager
from .render_context import apply_widget_render_metadata, with_widget_render_metadata
from .theme import THEME
from .url_params import is_valid_date, resolve_temporal_value

Position = Literal["sidebar", "inline", "bottom"]


def _normalize_date(value: str | None, fallback: str = "") -> str:
    if value is None:
        return fallback
    normalized = str(value).strip()
    if not normalized:
        return ""
    return normalized if is_valid_date(normalized) else fallback


def _normalize_bounds(min_value: str, max_value: str) -> tuple[str, str]:
    min_date = _normalize_date(min_value)
    max_date = _normalize_date(max_value)
    if min_date and max_date and min_date > max_date:
        warnings.warn("\nDateInput: `min` is greater than `max`. Swapping values.")
        min_date, max_date = max_date, min_date
    return min_date, max_date


def _normalize_value(value: str | None, min_value: str, max_value: str) -> str:
    date_value = _normalize_date(value)
    if value and not date_value:
        warnings.warn("\nDateInput: `value` is not a valid YYYY-MM-DD date. Defaulting to empty value.")
    if date_value and min_value and date_value < min_value:
        warnings.warn("\nDateInput: `value` is before `min`. Clamping to `min`.")
        return min_value
    if date_value and max_value and date_value > max_value:
        warnings.warn("\nDateInput: `value` is after `max`. Clamping to `max`.")
        return max_value
    return date_value


def DateInput(
    label: str = "Date",
    value: str = "",
    min: str = "",
    max: str = "",
    url_key: str = "",
    position: Position = "sidebar",
    disabled: bool = False,
    hidden: bool = False,
    key: str = "",
):
    """
    Create and display a date input widget.

    Values use the browser-native ISO date format: ``YYYY-MM-DD``.
    """
    min_date, max_date = _normalize_bounds(min, max)
    value_date = _normalize_value(value, min_date, max_date)
    value_date = resolve_temporal_value(value_date, url_key, validator=is_valid_date)
    value_date = _normalize_value(value_date, min_date, max_date)

    args = [label, value_date, min_date, max_date, url_key, position]
    kwargs = {
        "label": label,
        "value": value_date,
        "min": min_date,
        "max": max_date,
        "url_key": url_key,
        "position": position,
        "disabled": disabled,
        "hidden": hidden,
    }

    code_uid = WidgetsManager.get_code_uid("DateInput", key=key, args=args, kwargs=kwargs)
    cached = WidgetsManager.get_widget(code_uid)
    if cached:
        apply_widget_render_metadata(cached)
        display(cached)
        return cached

    instance = DateInputWidget(**with_widget_render_metadata(kwargs))
    WidgetsManager.add_widget(code_uid, instance)
    display(instance)
    return instance


class DateInputWidget(anywidget.AnyWidget):
    _esm = """
    function render({ model, el }) {
      const container = document.createElement("div");
      container.classList.add("mljar-date-container");

      const topLabel = document.createElement("div");
      topLabel.classList.add("mljar-date-label");

      const input = document.createElement("input");
      input.type = "date";
      input.classList.add("mljar-date-input");

      container.appendChild(topLabel);
      container.appendChild(input);
      el.appendChild(container);

      function syncFromModel() {
        topLabel.innerHTML = model.get("label") || "Date";
        input.value = model.get("value") || "";

        const min = model.get("min") || "";
        const max = model.get("max") || "";
        if (min) input.min = min; else input.removeAttribute("min");
        if (max) input.max = max; else input.removeAttribute("max");

        input.disabled = !!model.get("disabled");
        container.style.display = model.get("hidden") ? "none" : "flex";
      }

      input.addEventListener("change", () => {
        if (model.get("disabled")) return;
        model.set("value", input.value);
        model.save_changes();
      });

      model.on("change:value", syncFromModel);
      model.on("change:min", syncFromModel);
      model.on("change:max", syncFromModel);
      model.on("change:label", syncFromModel);
      model.on("change:disabled", syncFromModel);
      model.on("change:hidden", syncFromModel);

      syncFromModel();
    }
    export default { render };
    """

    _css = f"""
    .mljar-date-container {{
      display: flex;
      flex-direction: column;
      width: 100%;
      font-family: {THEME.get('font_family', 'Arial, sans-serif')};
      font-size: {THEME.get('font_size', '14px')};
      color: {THEME.get('text_color', '#222')};
      padding-left: 4px;
      padding-right: 4px;
      box-sizing: border-box;
    }}

    .mljar-date-label {{
      padding-top: 6px;
      margin-bottom: 4px;
      font-weight: 600;
    }}

    .mljar-date-input {{
      width: 100%;
      min-height: 40px;
      padding: 9px 10px;
      border: 1px solid {THEME.get('border_color', '#ccc')};
      border-radius: {THEME.get('border_radius', '6px')};
      background: {THEME.get('widget_background_color', '#fff')};
      color: {THEME.get('text_color', '#222')};
      box-sizing: border-box;
      line-height: 1.4;
    }}

    .mljar-date-input:disabled {{
      background: #f5f5f5;
      color: #888;
      cursor: not-allowed;
    }}

    .mljar-date-input:focus {{
      outline: none;
      border-color: {THEME.get('focus_border_color', THEME.get('accent_color', '#4c7cf0'))};
      border-width: 2px;
      box-shadow: none;
    }}

    @media (max-width: 768px) {{
      .mljar-date-input {{
        min-height: 44px;
        padding: 10px 12px;
      }}
    }}
    """

    value = traitlets.Unicode("").tag(sync=True)
    min = traitlets.Unicode("").tag(sync=True)
    max = traitlets.Unicode("").tag(sync=True)
    label = traitlets.Unicode("Date").tag(sync=True)
    url_key = traitlets.Unicode("").tag(sync=True)
    disabled = traitlets.Bool(False).tag(sync=True)
    hidden = traitlets.Bool(False).tag(sync=True)
    position = traitlets.Enum(
        values=["sidebar", "inline", "bottom"],
        default_value="sidebar",
        help="Widget placement: sidebar, inline, or bottom",
    ).tag(sync=True)
    cell_id = traitlets.Unicode(allow_none=True).tag(sync=True)
    source_cell_id = traitlets.Unicode(default_value=None, allow_none=True).tag(sync=True)
    render_slot_id = traitlets.Unicode(default_value=None, allow_none=True).tag(sync=True)
    layout_path = traitlets.Unicode(default_value=None, allow_none=True).tag(sync=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.min, self.max = _normalize_bounds(self.min, self.max)
        self.value = _normalize_value(self.value, self.min, self.max)

    def _repr_mimebundle_(self, **kwargs):
        data = super()._repr_mimebundle_(**kwargs)
        if len(data) > 1:
            data[0][MERCURY_MIMETYPE] = {
                "widget": type(self).__qualname__,
                "model_id": self.model_id,
                "position": self.position,
            }
            if "text/plain" in data[0]:
                del data[0]["text/plain"]
        return data
