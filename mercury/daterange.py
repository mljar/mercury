# Copyright MLJAR Sp. z o.o.
# Licensed under the Apache License, Version 2.0 (Apache-2.0)

import warnings
from typing import Literal, Sequence

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
        warnings.warn("\nDateRange: `min` is greater than `max`. Swapping values.")
        min_date, max_date = max_date, min_date
    return min_date, max_date


def _coerce_range(value: Sequence[str] | None) -> list[str]:
    if value is None:
        return ["", ""]
    if isinstance(value, (str, bytes)):
        return ["", ""]
    try:
        values = list(value)
    except TypeError:
        return ["", ""]
    start = values[0] if len(values) > 0 else ""
    end = values[1] if len(values) > 1 else ""
    return [str(start), str(end)]


def _normalize_range(value: Sequence[str] | None, min_value: str, max_value: str) -> list[str]:
    start_raw, end_raw = _coerce_range(value)
    start = _normalize_date(start_raw)
    end = _normalize_date(end_raw)

    if start_raw and not start:
        warnings.warn("\nDateRange: start value is not a valid YYYY-MM-DD date. Defaulting to empty value.")
    if end_raw and not end:
        warnings.warn("\nDateRange: end value is not a valid YYYY-MM-DD date. Defaulting to empty value.")

    if start and min_value and start < min_value:
        warnings.warn("\nDateRange: start value is before `min`. Clamping to `min`.")
        start = min_value
    if start and max_value and start > max_value:
        warnings.warn("\nDateRange: start value is after `max`. Clamping to `max`.")
        start = max_value
    if end and min_value and end < min_value:
        warnings.warn("\nDateRange: end value is before `min`. Clamping to `min`.")
        end = min_value
    if end and max_value and end > max_value:
        warnings.warn("\nDateRange: end value is after `max`. Clamping to `max`.")
        end = max_value

    if start and end and start > end:
        warnings.warn("\nDateRange: start value is after end value. Swapping values.")
        start, end = end, start

    return [start, end]


def DateRange(
    label: str = "Date range",
    value: Sequence[str] | None = None,
    min: str = "",
    max: str = "",
    start_url_key: str = "",
    end_url_key: str = "",
    position: Position = "sidebar",
    disabled: bool = False,
    hidden: bool = False,
    key: str = "",
):
    """
    Create and display a date range input widget.

    ``value`` is stored as ``["YYYY-MM-DD", "YYYY-MM-DD"]``.
    """
    min_date, max_date = _normalize_bounds(min, max)
    value_range = _normalize_range(value, min_date, max_date)
    value_range[0] = resolve_temporal_value(
        value_range[0],
        start_url_key,
        validator=is_valid_date,
    )
    value_range[1] = resolve_temporal_value(
        value_range[1],
        end_url_key,
        validator=is_valid_date,
    )
    value_range = _normalize_range(value_range, min_date, max_date)

    args = [label, tuple(value_range), min_date, max_date, start_url_key, end_url_key, position]
    kwargs = {
        "label": label,
        "value": value_range,
        "min": min_date,
        "max": max_date,
        "start_url_key": start_url_key,
        "end_url_key": end_url_key,
        "position": position,
        "disabled": disabled,
        "hidden": hidden,
    }

    code_uid = WidgetsManager.get_code_uid("DateRange", key=key, args=args, kwargs=kwargs)
    cached = WidgetsManager.get_widget(code_uid)
    if cached:
        apply_widget_render_metadata(cached)
        display(cached)
        return cached

    instance = DateRangeWidget(**with_widget_render_metadata(kwargs))
    WidgetsManager.add_widget(code_uid, instance)
    display(instance)
    return instance


class DateRangeWidget(anywidget.AnyWidget):
    _esm = """
    function render({ model, el }) {
      const container = document.createElement("div");
      container.classList.add("mljar-daterange-container");

      const topLabel = document.createElement("div");
      topLabel.classList.add("mljar-daterange-label");

      const row = document.createElement("div");
      row.classList.add("mljar-daterange-row");

      const start = document.createElement("input");
      start.type = "date";
      start.classList.add("mljar-daterange-input");
      start.setAttribute("aria-label", "Start date");

      const end = document.createElement("input");
      end.type = "date";
      end.classList.add("mljar-daterange-input");
      end.setAttribute("aria-label", "End date");

      row.appendChild(start);
      row.appendChild(end);
      container.appendChild(topLabel);
      container.appendChild(row);
      el.appendChild(container);

      function syncBounds(input) {
        const min = model.get("min") || "";
        const max = model.get("max") || "";
        if (min) input.min = min; else input.removeAttribute("min");
        if (max) input.max = max; else input.removeAttribute("max");
      }

      function syncFromModel() {
        topLabel.innerHTML = model.get("label") || "Date range";
        const value = model.get("value") || ["", ""];
        start.value = value[0] || "";
        end.value = value[1] || "";
        syncBounds(start);
        syncBounds(end);
        const disabled = !!model.get("disabled");
        start.disabled = disabled;
        end.disabled = disabled;
        container.style.display = model.get("hidden") ? "none" : "flex";
      }

      function saveRange() {
        if (model.get("disabled")) return;
        model.set("value", [start.value, end.value]);
        model.save_changes();
      }

      start.addEventListener("change", saveRange);
      end.addEventListener("change", saveRange);

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
    .mljar-daterange-container {{
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

    .mljar-daterange-label {{
      padding-top: 6px;
      margin-bottom: 4px;
      font-weight: 600;
    }}

    .mljar-daterange-row {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      width: 100%;
    }}

    .mljar-daterange-input {{
      width: 100%;
      min-width: 0;
      min-height: 40px;
      padding: 9px 10px;
      border: 1px solid {THEME.get('border_color', '#ccc')};
      border-radius: {THEME.get('border_radius', '6px')};
      background: {THEME.get('widget_background_color', '#fff')};
      color: {THEME.get('text_color', '#222')};
      box-sizing: border-box;
      line-height: 1.4;
    }}

    .mljar-daterange-input:disabled {{
      background: #f5f5f5;
      color: #888;
      cursor: not-allowed;
    }}

    .mljar-daterange-input:focus {{
      outline: none;
      border-color: {THEME.get('focus_border_color', THEME.get('accent_color', '#4c7cf0'))};
      box-shadow: none;
    }}

    @media (max-width: 768px) {{
      .mljar-daterange-input {{
        min-height: 44px;
        padding: 10px 12px;
      }}
    }}
    """

    value = traitlets.List(trait=traitlets.Unicode(), default_value=["", ""]).tag(sync=True)
    min = traitlets.Unicode("").tag(sync=True)
    max = traitlets.Unicode("").tag(sync=True)
    label = traitlets.Unicode("Date range").tag(sync=True)
    start_url_key = traitlets.Unicode("").tag(sync=True)
    end_url_key = traitlets.Unicode("").tag(sync=True)
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
        self.value = _normalize_range(self.value, self.min, self.max)

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
