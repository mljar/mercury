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
from .url_params import resolve_number_value

Position = Literal["sidebar", "inline", "bottom"]


def NumberInput(
    label: str = "Enter number",
    value: float | None = None,
    min: float = 0.0,
    max: float = 100.0,
    step: float = 1.0,
    url_key: str = "",
    position: Position = "sidebar",
    disabled: bool = False,
    hidden: bool = False,
    key: str = "",
):
    """
    Create and display a NumberInput widget.

    This function instantiates a `NumberInputWidget` with the given label and numeric
    constraints. If a widget with the same configuration (identified by a unique code UID
    generated from widget type, arguments, and keyword arguments) already exists in the
    `WidgetsManager`, the existing instance is returned and displayed.

    Notes on defaults and normalization
    -----------------------------------
    - If `value` is None, it defaults to `min`.
    - If `min > max`, values are swapped (with a warning).
    - If `step <= 0`, it defaults to 1 (with a warning).
    - If `value` is outside [min, max], it is clamped (with a warning).

    Parameters
    ----------
    label : str
        Text displayed above the input.
        The default is `"Enter number"`.
    value : float | None
        Initial value. If None, defaults to `min`.
    min : float
        Minimum allowed value.
        The default is 0.
    max : float
        Maximum allowed value.
        The default is 100.
    step : float
        Step used by the browser number input.
        The default is 1.
    url_key : str, optional
        URL query parameter name used to override the initial value.
        Missing, empty, or invalid values fall back to ``value``.
    position : {"sidebar", "inline", "bottom"}, optional
        Controls where the widget is displayed.
    disabled : bool, optional
        If `True`, the widget is visible but cannot be interacted with.
    hidden : bool, optional
        If `True`, the widget exists in the UI state but is not rendered.
    key : str, optional
        Unique identifier used to differentiate widgets with the same parameters.

    Returns
    -------
    NumberInputWidget
        The created or retrieved NumberInput widget instance.
    """

    # normalize min/max
    try:
        min_f = float(min)
        max_f = float(max)
    except Exception:
        raise Exception("NumberInput: `min` and `max` must be numbers.")

    if min_f > max_f:
        warnings.warn("\nNumberInput: `min` is greater than `max`. Swapping values.")
        min_f, max_f = max_f, min_f

    # normalize step
    try:
        step_f = float(step)
    except Exception:
        warnings.warn("\nNumberInput: `step` is not a number. Defaulting to 1.")
        step_f = 1.0

    if step_f <= 0:
        warnings.warn("\nNumberInput: `step` must be > 0. Defaulting to 1.")
        step_f = 1.0

    # normalize value
    if value is None:
        value_f = min_f
    else:
        try:
            value_f = float(value)
        except Exception:
            warnings.warn("\nNumberInput: `value` is not a number. Defaulting to `min`.")
            value_f = min_f

    if value_f < min_f or value_f > max_f:
        warnings.warn("\nNumberInput: `value` is out of range. Clamping to [min, max].")
        value_f = max(min_f, min(value_f, max_f))

    value_f = resolve_number_value(
        value=value_f,
        url_key=url_key,
        min_value=min_f,
        max_value=max_f,
        step=step_f,
    )

    args = [label, value_f, min_f, max_f, step_f, url_key, position, disabled, hidden]
    kwargs = {
        "label": label,
        "value": value_f,
        "min": min_f,
        "max": max_f,
        "step": step_f,
        "url_key": url_key,
        "position": position,
        "disabled": disabled,
        "hidden": hidden,
    }

    code_uid = WidgetsManager.get_code_uid("NumberInput", key=key, args=args, kwargs=kwargs)
    cached = WidgetsManager.get_widget(code_uid)
    if cached:
        apply_widget_render_metadata(cached)
        display(cached)
        return cached

    instance = NumberInputWidget(**with_widget_render_metadata(kwargs))
    WidgetsManager.add_widget(code_uid, instance)
    display(instance)
    return instance


class NumberInputWidget(anywidget.AnyWidget):
    _esm = """
    function render({ model, el }) {
      const container = document.createElement("div");
      container.classList.add("mljar-number-container");

      const topLabel = document.createElement("div");
      topLabel.classList.add("mljar-number-label");

      const fieldRow = document.createElement("div");
      fieldRow.classList.add("mljar-number-field-row");

      const input = document.createElement("input");
      input.type = "number";
      input.classList.add("mljar-number-input");

      const decrementBtn = document.createElement("button");
      decrementBtn.type = "button";
      decrementBtn.classList.add("mljar-number-step-btn", "mljar-number-step-down");
      decrementBtn.textContent = "-";
      decrementBtn.setAttribute("aria-label", "Decrease value");

      const incrementBtn = document.createElement("button");
      incrementBtn.type = "button";
      incrementBtn.classList.add("mljar-number-step-btn", "mljar-number-step-up");
      incrementBtn.textContent = "+";
      incrementBtn.setAttribute("aria-label", "Increase value");

      const controls = document.createElement("div");
      controls.classList.add("mljar-number-controls");

      controls.appendChild(decrementBtn);
      controls.appendChild(incrementBtn);
      fieldRow.appendChild(input);
      fieldRow.appendChild(controls);

      container.appendChild(topLabel);
      container.appendChild(fieldRow);
      el.appendChild(container);

      function clamp(val, min, max) {
        if (Number.isFinite(min) && val < min) return min;
        if (Number.isFinite(max) && val > max) return max;
        return val;
      }

      function normalizeStep(step) {
        return Number.isFinite(step) && step > 0 ? step : 1;
      }

      function commitValue(nextValue, saveNow = true) {
        const min = Number(model.get("min"));
        const max = Number(model.get("max"));
        let v = Number(nextValue);
        if (!Number.isFinite(v)) return;

        v = clamp(v, min, max);
        input.value = String(v);
        model.set("value", v);

        if (saveNow) {
          model.save_changes();
        }
      }

      function syncFromModel() {
        topLabel.innerHTML = model.get("label") || "Enter number";

        const min = Number(model.get("min"));
        const max = Number(model.get("max"));
        const step = Number(model.get("step"));

        if (Number.isFinite(min)) input.min = String(min); else input.removeAttribute("min");
        if (Number.isFinite(max)) input.max = String(max); else input.removeAttribute("max");
        if (Number.isFinite(step)) input.step = String(step); else input.removeAttribute("step");

        const v = Number(model.get("value"));
        input.value = Number.isFinite(v) ? String(v) : "";

        const disabled = !!model.get("disabled");
        input.disabled = disabled;
        incrementBtn.disabled = disabled;
        decrementBtn.disabled = disabled;

        const hidden = !!model.get("hidden");
        container.style.display = hidden ? "none" : "flex";
      }

      let debounceTimer = null;
      input.addEventListener("input", () => {
        if (model.get("disabled")) return;

        const min = Number(model.get("min"));
        const max = Number(model.get("max"));

        let v = Number(input.value);
        if (!Number.isFinite(v)) return;

        v = clamp(v, min, max);
        input.value = String(v);

        model.set("value", v);
        if (debounceTimer) clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => model.save_changes(), 200);
      });

      incrementBtn.addEventListener("click", () => {
        if (model.get("disabled")) return;
        const current = Number(model.get("value"));
        const step = normalizeStep(Number(model.get("step")));
        const base = Number.isFinite(current) ? current : 0;
        commitValue(base + step);
      });

      decrementBtn.addEventListener("click", () => {
        if (model.get("disabled")) return;
        const current = Number(model.get("value"));
        const step = normalizeStep(Number(model.get("step")));
        const base = Number.isFinite(current) ? current : 0;
        commitValue(base - step);
      });

      model.on("change:value", syncFromModel);
      model.on("change:min", syncFromModel);
      model.on("change:max", syncFromModel);
      model.on("change:step", syncFromModel);
      model.on("change:label", syncFromModel);
      model.on("change:disabled", syncFromModel);
      model.on("change:hidden", syncFromModel);

      syncFromModel();

      // ---- read cell id (no DOM modifications) ----
      /*
      const ID_ATTR = "data-cell-id";
      const hostWithId = el.closest(`[${ID_ATTR}]`);
      const cellId = hostWithId ? hostWithId.getAttribute(ID_ATTR) : null;

      if (cellId) {
        model.set("cell_id", cellId);
        model.save_changes();
        model.send({ type: "cell_id_detected", value: cellId });
      } else {
        const mo = new MutationObserver(() => {
          const host = el.closest(`[${ID_ATTR}]`);
          const newId = host?.getAttribute(ID_ATTR);
          if (newId) {
            model.set("cell_id", newId);
            model.save_changes();
            model.send({ type: "cell_id_detected", value: newId });
            mo.disconnect();
          }
        });
        mo.observe(document.body, { attributes: true, subtree: true, attributeFilter: [ID_ATTR] });
      }*/
    }
    export default { render };
    """

    _css = f"""
    .mljar-number-container {{
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

    .mljar-number-label {{
      margin-bottom: 4px;
      font-weight: 600;
    }}

    .mljar-number-field-row {{
      display: flex;
      align-items: stretch;
      width: 100%;
      min-height: 40px;
      border: 1px solid {THEME.get('border_color', '#ccc')};
      border-radius: {THEME.get('border_radius', '6px')};
      background: {THEME.get('widget_background_color', '#fff')};
      box-sizing: border-box;
      overflow: hidden;
    }}

    .mljar-number-input {{
      flex: 1 1 auto;
      min-width: 0;
      min-height: 100%;
      padding: 7px 10px;
      border: 0;
      border-radius: 0;
      background: {THEME.get('widget_background_color', '#fff')};
      box-sizing: border-box;
      background-color: {THEME.get('widget_background_color', '#fff')} !important;
      color: {THEME.get('text_color', '#222')} !important;
      font: inherit;
      line-height: 1.2;
      -moz-appearance: textfield;
    }}

    .mljar-number-input::-webkit-outer-spin-button,
    .mljar-number-input::-webkit-inner-spin-button {{
      -webkit-appearance: none;
      margin: 0;
    }}

    .mljar-number-input:disabled {{
      background: #f5f5f5;
      color: #888;
      cursor: not-allowed;
    }}

    .mljar-number-input:focus {{
      outline: none;
    }}

    .mljar-number-field-row:focus-within {{
      border-color: {THEME.get('focus_border_color', THEME.get('accent_color', '#4c7cf0'))};
      border-width: 2px;
      box-shadow: none;
    }}

    .mljar-number-field-row:focus-within .mljar-number-controls {{
      border-left-color: {THEME.get('focus_border_color', THEME.get('accent_color', '#4c7cf0'))};
    }}

    .mljar-number-controls {{
      display: flex;
      align-items: stretch;
      flex: 0 0 auto;
      border-left: 1px solid {THEME.get('border_color', '#ccc')};
      background: {THEME.get('panel_bg_hover', '#f7f7f7')};
    }}

    .mljar-number-step-btn {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 38px;
      min-width: 38px;
      min-height: 100%;
      border: 0;
      border-radius: 0;
      background: transparent;
      color: {THEME.get('text_color', '#222')};
      font: inherit;
      font-size: 18px;
      font-weight: 700;
      line-height: 1;
      cursor: pointer;
      padding: 0;
      user-select: none;
      -webkit-user-select: none;
      touch-action: manipulation;
      transition: background-color 0.14s ease, color 0.14s ease;
    }}

    .mljar-number-step-up {{
      border-left: 1px solid {THEME.get('border_color', '#ccc')};
    }}

    .mljar-number-step-btn:hover {{
      background: {THEME.get('hover_background_color', '#ececec')};
    }}

    .mljar-number-step-btn:active {{
      background: {THEME.get('selected_background_color', '#e0e0e0')};
      color: {THEME.get('accent_color', '#1f4fd1')};
    }}

    .mljar-number-step-btn:focus-visible {{
      outline: none;
      background: {THEME.get('selected_background_color', '#e0e0e0')};
      color: {THEME.get('accent_color', '#1f4fd1')};
    }}

    .mljar-number-step-btn:disabled {{
      background: #f5f5f5;
      color: #aaa;
      cursor: not-allowed;
    }}

    @media (max-width: 768px) {{
      .mljar-number-field-row {{
        min-height: 44px;
      }}

      .mljar-number-input {{
        min-height: 44px;
        padding: 8px 12px;
      }}

      .mljar-number-step-btn {{
        font-size: 19px;
        width: 44px;
        min-width: 44px;
      }}
    }}
    """

    value = traitlets.Float(0.0).tag(sync=True)
    min = traitlets.Float(0.0).tag(sync=True)
    max = traitlets.Float(100.0).tag(sync=True)
    step = traitlets.Float(1.0).tag(sync=True)
    label = traitlets.Unicode("Enter number").tag(sync=True)
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

        # normalize again in case instantiated directly
        if self.min > self.max:
            self.min, self.max = self.max, self.min

        if self.value is None:
            self.value = self.min

        if self.value < self.min:
            self.value = self.min
        if self.value > self.max:
            self.value = self.max

        if self.step is None or self.step <= 0:
            self.step = 1.0

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
