# Copyright MLJAR Sp. z o.o.
# Licensed under the Apache License, Version 2.0 (Apache-2.0)

from typing import Literal

import anywidget
import traitlets
from IPython.display import display

from .manager import MERCURY_MIMETYPE, WidgetsManager
from .theme import THEME

Position = Literal["sidebar", "inline", "bottom"]


def TextInput(
    label: str = "Enter text",
    value: str = "",
    position: Position = "sidebar",
    disabled: bool = False,
    hidden: bool = False,
    key: str = "",
):
    """
    Create and display a TextInput widget.

    This function instantiates a `TextInputWidget`. If a widget with the same
    configuration already exists in `WidgetsManager`, the cached instance is reused.

    Parameters
    ----------
    label : str
        Text displayed above the input.
        The default is `"Enter text"`.
    value : str
        Initial value.
        The default is `""`.
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
    TextInputWidget
        The created or retrieved TextInput widget instance.
    """

    args = [label, value, position]
    kwargs = {
        "label": label,
        "value": value,
        "position": position
    }

    code_uid = WidgetsManager.get_code_uid("TextInput", key=key, args=args, kwargs=kwargs)
    cached = WidgetsManager.get_widget(code_uid)
    if cached:
        display(cached)
        return cached

    instance = TextInputWidget(**kwargs)
    WidgetsManager.add_widget(code_uid, instance)
    display(instance)
    return instance


class TextInputWidget(anywidget.AnyWidget):
    _esm = """
    function render({ model, el }) {
      const container = document.createElement("div");
      container.classList.add("mljar-textinput-container");

      const topLabel = document.createElement("div");
      topLabel.classList.add("mljar-textinput-top-label");

      const input = document.createElement("input");
      input.type = "text";
      input.classList.add("mljar-textinput-input");

      container.appendChild(topLabel);
      container.appendChild(input);
      el.appendChild(container);

      let debounceTimer = null;

      input.addEventListener("input", () => {
        if (model.get("disabled")) return;
        model.set("value", input.value);
        if (debounceTimer) clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => model.save_changes(), 200);
      });

      function syncFromModel() {
        topLabel.innerHTML = model.get("label") || "Enter text";
        input.value = model.get("value") ?? "";

        const disabled = !!model.get("disabled");
        input.disabled = disabled;

        const hidden = !!model.get("hidden");
        container.style.display = hidden ? "none" : "flex";
      }

      model.on("change:value", syncFromModel);
      model.on("change:label", syncFromModel);
      model.on("change:disabled", syncFromModel);
      model.on("change:hidden", syncFromModel);

      syncFromModel();

      /*
      // ---- read cell id (no DOM modifications) ----
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
      }
      */
    }
    export default { render };
    """

    _css = f"""
    .mljar-textinput-container {{
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

    .mljar-textinput-top-label {{
      margin-bottom: 6px;
      text-align: left;
      width: 100%;
      font-weight: 600;
    }}

    .mljar-textinput-input {{
      width: 100%;
      padding: 6px 10px;
      min-height: 1.6em;
      box-sizing: border-box;
      border: {"1px solid " + THEME.get('border_color', '#ccc') if THEME.get('border_visible', True) else "none"};
      border-radius: {THEME.get('border_radius', '6px')};
      background: {THEME.get('widget_background_color', '#fff')};
      color: {THEME.get('text_color', '#222')};

      appearance: none !important;
      background-color: {THEME.get('widget_background_color', '#fff')} !important;
    }}

    .mljar-textinput-input:focus {{
      outline: none;
      border-color: {THEME.get('primary_color', '#007bff')};
    }}

    .mljar-textinput-input:disabled {{
      background: #f5f5f5;
      color: #888;
      cursor: not-allowed;
    }}
    """

    value = traitlets.Unicode("").tag(sync=True)
    label = traitlets.Unicode("Enter text").tag(sync=True)

    disabled = traitlets.Bool(False).tag(sync=True)
    hidden = traitlets.Bool(False).tag(sync=True)

    position = traitlets.Enum(
        values=["sidebar", "inline", "bottom"],
        default_value="sidebar",
        help="Widget placement: sidebar, inline, or bottom",
    ).tag(sync=True)

    cell_id = traitlets.Unicode(allow_none=True).tag(sync=True)

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
