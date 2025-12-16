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


def Slider(
    label: str = "Select number",
    value: int | None = None,
    min: int = 0,
    max: int = 100,
    position: Position = "sidebar",
    disabled: bool = False,
    hidden: bool = False,
    key: str = "",
):
    """
    Create and display a Slider widget.

    This function instantiates a `SliderWidget` with the given label and range.
    If a widget with the same configuration (identified by a unique code UID
    generated from widget type, arguments, and keyword arguments) already exists
    in the `WidgetsManager`, the existing instance is returned and displayed.

    Notes on defaults and normalization
    -----------------------------------
    - If `value` is None, it defaults to `min`.
    - If `min > max`, values are swapped (with a warning).
    - If `value` is outside [min, max], it is clamped (with a warning).

    Parameters
    ----------
    label : str
        Text displayed above the widget.
        The default is `"Select number"`.
    value : int | None
        Initial value. If None, defaults to `min`.
    min : int
        Minimum slider value.
        The default is 0.
    max : int
        Maximum slider value.
        The default is 100.
    position : {"sidebar", "inline", "bottom"}, optional
        Controls where the widget is displayed:

        - `"sidebar"` — place the widget in the left sidebar panel (default).
        - `"inline"` — render the widget directly in the notebook flow.
        - `"bottom"` — render the widget after all notebook cells.
    disabled : bool, optional
        If `True`, the widget is rendered but cannot be interacted with.
    hidden : bool, optional
        If `True`, the widget exists but is not visible in the UI.
    key : str, optional
        Unique identifier used to differentiate widgets with the same parameters.

    Returns
    -------
    SliderWidget
        The created or retrieved Slider widget instance.

    Examples
    --------
    Basic usage:

    >>> from mercury import Slider
    >>> s = Slider(label="Rows", min=0, max=100, value=10)
    >>> s.value
    10

    After user interaction in the UI:

    >>> s.value
    42
    """

    # Validate and normalize range
    try:
        min_int = int(min)
        max_int = int(max)
    except Exception:
        raise Exception("Slider: `min` and `max` must be integers.")

    if min_int > max_int:
        warnings.warn("\nSlider: `min` is greater than `max`. Swapping values.")
        min_int, max_int = max_int, min_int

    # Normalize value
    if value is None:
        value_int = min_int
    else:
        try:
            value_int = int(value)
        except Exception:
            warnings.warn("\nSlider: `value` is not an integer. Defaulting to `min`.")
            value_int = min_int

    if value_int < min_int or value_int > max_int:
        warnings.warn("\nSlider: `value` is out of range. Clamping to [min, max].")
        value_int = max(min_int, min(value_int, max_int))

    args = [label, value_int, min_int, max_int, position]
    kwargs = {
        "label": label,
        "value": value_int,
        "min": min_int,
        "max": max_int,
        "position": position
    }

    code_uid = WidgetsManager.get_code_uid("Slider", key=key, args=args, kwargs=kwargs)
    cached = WidgetsManager.get_widget(code_uid)
    if cached:
        display(cached)
        return cached

    instance = SliderWidget(**kwargs)
    WidgetsManager.add_widget(code_uid, instance)
    display(instance)
    return instance


class SliderWidget(anywidget.AnyWidget):
    _esm = """
    function render({ model, el }) {
      const container = document.createElement("div");
      container.classList.add("mljar-slider-container");

      const topLabel = document.createElement("div");
      topLabel.classList.add("mljar-slider-top-label");

      const sliderRow = document.createElement("div");
      sliderRow.classList.add("mljar-slider-row");

      const slider = document.createElement("input");
      slider.type = "range";
      slider.classList.add("mljar-slider-input");

      const valueLabel = document.createElement("span");
      valueLabel.classList.add("mljar-slider-value-label");

      function syncFromModel() {
        slider.min = model.get("min");
        slider.max = model.get("max");
        slider.value = model.get("value");
        valueLabel.textContent = String(model.get("value"));

        slider.disabled = !!model.get("disabled");
        topLabel.textContent = model.get("label") || "Select number";

        // hidden (exists but not visible)
        container.style.display = model.get("hidden") ? "none" : "flex";
      }

      let debounceTimer = null;
      slider.addEventListener("input", () => {
        if (model.get("disabled")) return;
        model.set("value", Number(slider.value));
        if (debounceTimer) clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
          model.save_changes();
        }, 100);
      });

      model.on("change:value", syncFromModel);
      model.on("change:min", syncFromModel);
      model.on("change:max", syncFromModel);
      model.on("change:disabled", syncFromModel);
      model.on("change:hidden", syncFromModel);
      model.on("change:label", syncFromModel);

      sliderRow.appendChild(slider);
      sliderRow.appendChild(valueLabel);

      container.appendChild(topLabel);
      container.appendChild(sliderRow);
      el.appendChild(container);

      syncFromModel();

      // ---- read cell id (no DOM modifications) ----
      /*const ID_ATTR = "data-cell-id";
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
    .mljar-slider-container {{
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      width: 100%;
      min-width: 120px;
      font-family: {THEME.get('font_family', 'Arial, sans-serif')};
      font-size: {THEME.get('font_size', '14px')};
      font-weight: {THEME.get('font_weight', 'normal')};
      color: {THEME.get('text_color', '#222')};
      margin-bottom: 8px;
      padding-left: 4px;
      padding-right: 4px;
      box-sizing: border-box;
    }}

    .mljar-slider-top-label {{
      margin-bottom: 6px;
      font-weight: 600;
    }}

    .mljar-slider-row {{
      display: grid;
      grid-template-columns: 1fr 5ch;
      column-gap: 16px;
      align-items: center;
      width: 100%;
      overflow: visible;
      box-sizing: border-box;
    }}

    .mljar-slider-input {{
      width: 100%;
      min-width: 60px;
      max-width: 100%;
      background: transparent;
      -webkit-appearance: none;
      appearance: none;
      border: none;
      height: 24px;
      padding: 0;
      margin: 0;
      box-sizing: border-box;
    }}

    .mljar-slider-input:focus {{
      outline: none;
    }}

    /* Track */
    .mljar-slider-input::-webkit-slider-runnable-track {{
      height: 6px;
      background: {THEME.get('slider_track_color', '#e0e0e0')};
      border-radius: {THEME.get('border_radius', '6px')};
      margin: auto;
    }}
    .mljar-slider-input::-moz-range-track {{
      height: 6px;
      background: {THEME.get('slider_track_color', '#e0e0e0')};
      border-radius: {THEME.get('border_radius', '6px')};
    }}

    /* Thumb */
    .mljar-slider-input::-webkit-slider-thumb {{
      -webkit-appearance: none;
      appearance: none;
      width: 16px;
      height: 16px;
      border-radius: 50%;
      background: {THEME.get('primary_color', '#007bff')};
      cursor: pointer;
      margin-top: -5px;
    }}
    .mljar-slider-input::-moz-range-thumb {{
      width: 16px;
      height: 16px;
      border-radius: 50%;
      background: {THEME.get('primary_color', '#007bff')};
      cursor: pointer;
    }}

    .mljar-slider-value-label {{
      width: 5ch;
      text-align: right;
      font-weight: 700;
      font-size: 1.1em;
      color: {THEME.get('text_color', '#000')};
      white-space: nowrap;
      line-height: 1;
    }}
    """

    value = traitlets.Int(0).tag(sync=True)
    min = traitlets.Int(0).tag(sync=True)
    max = traitlets.Int(100).tag(sync=True)
    label = traitlets.Unicode("Select number").tag(sync=True)

    disabled = traitlets.Bool(default_value=False).tag(sync=True)
    hidden = traitlets.Bool(default_value=False).tag(sync=True)

    position = traitlets.Enum(
        values=["sidebar", "inline", "bottom"],
        default_value="sidebar",
        help="Widget placement: sidebar, inline, or bottom",
    ).tag(sync=True)

    cell_id = traitlets.Unicode(allow_none=True).tag(sync=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Range normalization (in case widget is instantiated directly)
        if self.min > self.max:
            self.min, self.max = self.max, self.min

        # Default to min if missing
        if self.value is None:
            self.value = self.min

        # Clamp
        if self.value < self.min:
            self.value = self.min
        if self.value > self.max:
            self.value = self.max

    def _repr_mimebundle_(self, **kwargs):
        data = super()._repr_mimebundle_(**kwargs)
        if len(data) > 1:
            mercury_mime = {
                "widget": type(self).__qualname__,
                "model_id": self.model_id,
                "position": self.position,
            }
            data[0][MERCURY_MIMETYPE] = mercury_mime
            if "text/plain" in data[0]:
                del data[0]["text/plain"]
        return data
