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
from .url_params import resolve_integer_value

Position = Literal["sidebar", "inline", "bottom"]


def Slider(
    label: str = "Select number",
    value: int | None = None,
    min: int = 0,
    max: int = 100,
    url_key: str = "",
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
    url_key : str, optional
        URL query parameter name used to override the initial value.
        Missing, empty, or invalid values fall back to ``value``.
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
        if value_int < min_int:
            value_int = min_int
        if value_int > max_int:
            value_int = max_int

    value_int = resolve_integer_value(
        value=value_int,
        url_key=url_key,
        min_value=min_int,
        max_value=max_int,
    )

    args = [label, value_int, min_int, max_int, url_key, position, disabled, hidden]
    kwargs = {
        "label": label,
        "value": value_int,
        "min": min_int,
        "max": max_int,
        "url_key": url_key,
        "position": position,
        "disabled": disabled,
        "hidden": hidden,
    }

    code_uid = WidgetsManager.get_code_uid("Slider", key=key, args=args, kwargs=kwargs)
    cached = WidgetsManager.get_widget(code_uid)
    if cached:
        apply_widget_render_metadata(cached)
        display(cached)
        return cached

    instance = SliderWidget(**with_widget_render_metadata(kwargs))
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

      const sliderStage = document.createElement("div");
      sliderStage.classList.add("mljar-slider-stage");

      const floatingValueLabel = document.createElement("div");
      floatingValueLabel.classList.add("mljar-slider-floating-value");

      const sliderRow = document.createElement("div");
      sliderRow.classList.add("mljar-slider-row");

      const slider = document.createElement("input");
      slider.type = "range";
      slider.classList.add("mljar-slider-input");

      const minMaxRow = document.createElement("div");
      minMaxRow.classList.add("mljar-slider-minmax-row");

      const minLabel = document.createElement("span");
      minLabel.classList.add("mljar-slider-min-label");

      const maxLabel = document.createElement("span");
      maxLabel.classList.add("mljar-slider-max-label");

      function positionFloatingValue() {
        const min = Number(model.get("min"));
        const max = Number(model.get("max"));
        const value = Number(model.get("value"));
        const range = max - min;
        const ratio = range <= 0 ? 0 : (value - min) / range;
        const clampedRatio = Math.max(0, Math.min(1, ratio));
        const computed = getComputedStyle(container);
        const thumbSize =
          parseFloat(computed.getPropertyValue("--mljar-slider-thumb-size")) || 16;
        const inputWidth = slider.clientWidth || 0;
        const stageWidth = sliderStage.clientWidth || inputWidth || 0;
        const labelWidth = floatingValueLabel.offsetWidth || 0;

        if (inputWidth <= 0 || stageWidth <= 0) {
          return;
        }

        const sliderOffsetLeft = slider.offsetLeft || 0;
        const usableWidth = Math.max(0, inputWidth - thumbSize);
        const idealCenter =
          sliderOffsetLeft + thumbSize / 2 + clampedRatio * usableWidth;
        const halfLabel = labelWidth / 2;
        const minCenter = halfLabel;
        const maxCenter = Math.max(halfLabel, stageWidth - halfLabel);
        const finalCenter = Math.min(Math.max(idealCenter, minCenter), maxCenter);

        floatingValueLabel.style.left = `${finalCenter}px`;
      }

      function syncFromModel() {
        slider.min = model.get("min");
        slider.max = model.get("max");
        slider.value = model.get("value");
        floatingValueLabel.textContent = String(model.get("value"));
        minLabel.textContent = String(model.get("min"));
        maxLabel.textContent = String(model.get("max"));

        slider.disabled = !!model.get("disabled");
        topLabel.textContent = model.get("label") || "Select number";

        // hidden (exists but not visible)
        container.style.display = model.get("hidden") ? "none" : "flex";
        positionFloatingValue();
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
      minMaxRow.appendChild(minLabel);
      minMaxRow.appendChild(maxLabel);

      container.appendChild(topLabel);
      sliderStage.appendChild(floatingValueLabel);
      sliderStage.appendChild(sliderRow);
      sliderStage.appendChild(minMaxRow);
      container.appendChild(sliderStage);
      el.appendChild(container);

      syncFromModel();

      const resizeObserver = new ResizeObserver(() => {
        positionFloatingValue();
      });
      resizeObserver.observe(sliderStage);

      return () => {
        resizeObserver.disconnect();
      };

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
      --mljar-slider-thumb-size: 16px;
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      gap: 0;
      width: 100%;
      max-width: 100%;
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

    .mljar-slider-stage {{
      position: relative;
      width: 100%;
      max-width: 100%;
      min-width: 0;
      padding-top: 20px;
      overflow: visible;
      box-sizing: border-box;
    }}

    .mljar-slider-floating-value {{
      position: absolute;
      top: 0;
      left: 8px;
      transform: translateX(-50%);
      color: {THEME.get('primary_color', '#007bff')};
      font-weight: 700;
      font-size: 0.95em;
      line-height: 1;
      text-align: center;
      white-space: nowrap;
      pointer-events: none;
      z-index: 1;
    }}

    .mljar-slider-top-label {{
      margin-bottom: 6px;
      font-weight: 600;
      line-height: 1.2;
    }}

    .mljar-slider-row {{
      position: relative;
      width: 100%;
      max-width: 100%;
      min-width: 0;
      overflow: visible;
      box-sizing: border-box;
    }}

    .mljar-slider-minmax-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      width: 100%;
      max-width: 100%;
      min-width: 0;
      margin-top: 6px;
      color: {THEME.get('muted_text_color', '#8a8f98')};
      font-size: 0.9em;
      line-height: 1.2;
      box-sizing: border-box;
    }}

    .mljar-slider-min-label,
    .mljar-slider-max-label {{
      color: inherit;
      white-space: nowrap;
    }}

    .mljar-slider-input {{
      display: block;
      width: 100%;
      max-width: 100%;
      min-width: 0;
      background: transparent;
      -webkit-appearance: none;
      appearance: none;
      border: none;
      height: 24px;
      padding: 0;
      margin: 0;
      cursor: pointer;
      box-sizing: border-box;
    }}

    .mljar-slider-input:focus {{
      outline: none;
    }}

    .mljar-slider-input:focus-visible::-webkit-slider-thumb {{
      box-shadow: 0 0 0 3px {THEME.get('selected_background_color', '#eef3ff')};
    }}
    .mljar-slider-input:focus-visible::-moz-range-thumb {{
      box-shadow: 0 0 0 3px {THEME.get('selected_background_color', '#eef3ff')};
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
      width: var(--mljar-slider-thumb-size);
      height: var(--mljar-slider-thumb-size);
      border-radius: 50%;
      background: {THEME.get('primary_color', '#007bff')};
      cursor: pointer;
      margin-top: -5px;
      transition: transform 0.14s ease, background-color 0.14s ease;
    }}
    .mljar-slider-input::-moz-range-thumb {{
      width: var(--mljar-slider-thumb-size);
      height: var(--mljar-slider-thumb-size);
      border-radius: 50%;
      background: {THEME.get('primary_color', '#007bff')};
      cursor: pointer;
      transition: transform 0.14s ease, background-color 0.14s ease;
    }}

    .mljar-slider-input:disabled {{
      cursor: not-allowed;
      opacity: 0.7;
    }}

    .mljar-slider-input:disabled::-webkit-slider-thumb {{
      cursor: not-allowed;
      transform: none;
    }}

    .mljar-slider-input:disabled::-moz-range-thumb {{
      cursor: not-allowed;
      transform: none;
    }}

    .mljar-slider-input:active::-webkit-slider-thumb {{
      transform: scale(1.08);
      background: {THEME.get('accent_color', THEME.get('primary_color', '#007bff'))};
    }}
    .mljar-slider-input:active::-moz-range-thumb {{
      transform: scale(1.08);
      background: {THEME.get('accent_color', THEME.get('primary_color', '#007bff'))};
    }}
    """

    value = traitlets.Int(0).tag(sync=True)
    min = traitlets.Int(0).tag(sync=True)
    max = traitlets.Int(100).tag(sync=True)
    label = traitlets.Unicode("Select number").tag(sync=True)
    url_key = traitlets.Unicode("").tag(sync=True)

    disabled = traitlets.Bool(default_value=False).tag(sync=True)
    hidden = traitlets.Bool(default_value=False).tag(sync=True)

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
