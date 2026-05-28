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
from .url_params import is_valid_time, resolve_temporal_value

Position = Literal["sidebar", "inline", "bottom"]


def _normalize_time(value: str | None, fallback: str = "") -> str:
    if value is None:
        return fallback
    normalized = str(value).strip()
    if not normalized:
        return ""
    return normalized if is_valid_time(normalized) else fallback


def _normalize_bounds(min_value: str, max_value: str) -> tuple[str, str]:
    min_time = _normalize_time(min_value)
    max_time = _normalize_time(max_value)
    if min_time and max_time and min_time > max_time:
        warnings.warn("\nTimeInput: `min` is greater than `max`. Swapping values.")
        min_time, max_time = max_time, min_time
    return min_time, max_time


def _normalize_step(step: int | None) -> int:
    if step is None:
        return 60
    try:
        step_int = int(step)
    except Exception:
        warnings.warn("\nTimeInput: `step` is not an integer. Defaulting to 60.")
        return 60
    if step_int <= 0:
        warnings.warn("\nTimeInput: `step` must be > 0. Defaulting to 60.")
        return 60
    return step_int


def _normalize_value(value: str | None, min_value: str, max_value: str) -> str:
    time_value = _normalize_time(value)
    if value and not time_value:
        warnings.warn("\nTimeInput: `value` is not a valid HH:MM or HH:MM:SS time. Defaulting to empty value.")
    if time_value and min_value and time_value < min_value:
        warnings.warn("\nTimeInput: `value` is before `min`. Clamping to `min`.")
        return min_value
    if time_value and max_value and time_value > max_value:
        warnings.warn("\nTimeInput: `value` is after `max`. Clamping to `max`.")
        return max_value
    return time_value


def TimeInput(
    label: str = "Time",
    value: str = "",
    min: str = "",
    max: str = "",
    step: int = 60,
    url_key: str = "",
    position: Position = "sidebar",
    disabled: bool = False,
    hidden: bool = False,
    key: str = "",
):
    """
    Create and display a time input widget.

    Values use browser-native ``HH:MM`` or ``HH:MM:SS`` strings.
    """
    min_time, max_time = _normalize_bounds(min, max)
    step_int = _normalize_step(step)
    value_time = _normalize_value(value, min_time, max_time)
    value_time = resolve_temporal_value(value_time, url_key, validator=is_valid_time)
    value_time = _normalize_value(value_time, min_time, max_time)

    args = [label, value_time, min_time, max_time, step_int, url_key, position]
    kwargs = {
        "label": label,
        "value": value_time,
        "min": min_time,
        "max": max_time,
        "step": step_int,
        "url_key": url_key,
        "position": position,
        "disabled": disabled,
        "hidden": hidden,
    }

    code_uid = WidgetsManager.get_code_uid("TimeInput", key=key, args=args, kwargs=kwargs)
    cached = WidgetsManager.get_widget(code_uid)
    if cached:
        apply_widget_render_metadata(cached)
        display(cached)
        return cached

    instance = TimeInputWidget(**with_widget_render_metadata(kwargs))
    WidgetsManager.add_widget(code_uid, instance)
    display(instance)
    return instance


class TimeInputWidget(anywidget.AnyWidget):
    _esm = """
    function render({ model, el }) {
      const container = document.createElement("div");
      container.classList.add("mljar-time-container");

      const topLabel = document.createElement("div");
      topLabel.classList.add("mljar-time-label");

      const input = document.createElement("input");
      input.type = "time";
      input.classList.add("mljar-time-input");

      container.appendChild(topLabel);
      container.appendChild(input);
      el.appendChild(container);

      function syncFromModel() {
        topLabel.innerHTML = model.get("label") || "Time";
        input.value = model.get("value") || "";
        const min = model.get("min") || "";
        const max = model.get("max") || "";
        if (min) input.min = min; else input.removeAttribute("min");
        if (max) input.max = max; else input.removeAttribute("max");
        input.step = String(model.get("step") || 60);
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
      model.on("change:step", syncFromModel);
      model.on("change:label", syncFromModel);
      model.on("change:disabled", syncFromModel);
      model.on("change:hidden", syncFromModel);

      syncFromModel();
    }
    export default { render };
    """

    _css = f"""
    .mljar-time-container {{
      display: flex;
      flex-direction: column;
      width: 100%;
      font-family: {THEME.get('font_family', 'Arial, sans-serif')};
      font-size: {THEME.get('font_size', '14px')};
      color: {THEME.get('text_color', '#222')};
      margin-bottom: 8px;
      padding-left: 4px;
      padding-right: 4px;
      box-sizing: border-box;
    }}

    .mljar-time-label {{
      margin-bottom: 4px;
      font-weight: 600;
    }}

    .mljar-time-input {{
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

    .mljar-time-input:disabled {{
      background: #f5f5f5;
      color: #888;
      cursor: not-allowed;
    }}

    .mljar-time-input:focus {{
      outline: none;
      border-color: {THEME.get('accent_color', '#4c7cf0')};
      border-width: 2px;
      box-shadow: none;
    }}

    @media (max-width: 768px) {{
      .mljar-time-input {{
        min-height: 44px;
        padding: 10px 12px;
      }}
    }}
    """

    value = traitlets.Unicode("").tag(sync=True)
    min = traitlets.Unicode("").tag(sync=True)
    max = traitlets.Unicode("").tag(sync=True)
    step = traitlets.Int(60).tag(sync=True)
    label = traitlets.Unicode("Time").tag(sync=True)
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
        self.step = _normalize_step(self.step)
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
