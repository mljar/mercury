# Copyright MLJAR Sp. z o.o.
# Licensed under the Apache License, Version 2.0 (Apache-2.0)

import warnings
from typing import Literal

import anywidget
import traitlets
from IPython.display import display

from .manager import MERCURY_MIMETYPE, WidgetsManager
from .theme import THEME

Position = Literal["sidebar", "inline", "bottom"]


def NumberInput(
    label: str = "Enter number",
    value: float | None = None,
    min: float = 0.0,
    max: float = 100.0,
    step: float = 1.0,
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

    args = [label, value_f, min_f, max_f, step_f, position]
    kwargs = {
        "label": label,
        "value": value_f,
        "min": min_f,
        "max": max_f,
        "step": step_f,
        "position": position
    }

    code_uid = WidgetsManager.get_code_uid("NumberInput", key=key, args=args, kwargs=kwargs)
    cached = WidgetsManager.get_widget(code_uid)
    if cached:
        display(cached)
        return cached

    instance = NumberInputWidget(**kwargs)
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

      const input = document.createElement("input");
      input.type = "number";
      input.classList.add("mljar-number-input");

      container.appendChild(topLabel);
      container.appendChild(input);
      el.appendChild(container);

      function clamp(val, min, max) {
        if (Number.isFinite(min) && val < min) return min;
        if (Number.isFinite(max) && val > max) return max;
        return val;
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

    .mljar-number-input {{
      width: 100%;
      padding: 6px;
      border: 1px solid {THEME.get('border_color', '#ccc')};
      border-radius: {THEME.get('border_radius', '6px')};
      background: #fff;
      box-sizing: border-box;

      appearance: none !important;
      background-color: #ffffff !important;
      color: {THEME.get('text_color', '#222')} !important;
    }}

    .mljar-number-input:disabled {{
      background: #f5f5f5;
      color: #888;
      cursor: not-allowed;
    }}
    """

    value = traitlets.Float(0.0).tag(sync=True)
    min = traitlets.Float(0.0).tag(sync=True)
    max = traitlets.Float(100.0).tag(sync=True)
    step = traitlets.Float(1.0).tag(sync=True)
    label = traitlets.Unicode("Enter number").tag(sync=True)

    disabled = traitlets.Bool(False).tag(sync=True)
    hidden = traitlets.Bool(False).tag(sync=True)

    position = traitlets.Enum(
        values=["sidebar", "inline", "bottom"],
        default_value="sidebar",
        help="Widget placement: sidebar, inline, or bottom",
    ).tag(sync=True)

    cell_id = traitlets.Unicode(allow_none=True).tag(sync=True)

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
