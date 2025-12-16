# Copyright MLJAR Sp. z o.o.
# Licensed under the Apache License, Version 2.0 (Apache-2.0)

from typing import Literal

import anywidget
import traitlets
from IPython.display import display

from .manager import MERCURY_MIMETYPE, WidgetsManager
from .theme import THEME

Position = Literal["sidebar", "inline", "bottom"]
Appearance = Literal["toggle", "box"]


def CheckBox(
    label: str = "Enable",
    value: bool = False,
    appearance: Appearance = "toggle",
    position: Position = "sidebar",
    disabled: bool = False,
    hidden: bool = False,
    key: str = "",
):
    """
    Create and display a Checkbox widget.

    Examples
    --------
    >>> import mercury as mr
    >>> cb = mr.Checkbox(label="Auto-refresh")               # toggle (default)
    >>> cb2 = mr.Checkbox(label="I agree", appearance="box") # classic box
    >>> cb.value
    False
    """

    args = [label, bool(value), appearance, position]
    kwargs = {
        "label": label,
        "value": bool(value),
        "appearance": appearance,
        "position": position
    }

    code_uid = WidgetsManager.get_code_uid("Checkbox", key=key, args=args, kwargs=kwargs)
    cached = WidgetsManager.get_widget(code_uid)
    
    if cached:
        display(cached)
        return cached

    instance = CheckboxWidget(**kwargs)
    WidgetsManager.add_widget(code_uid, instance)
    display(instance)
    return instance


class CheckboxWidget(anywidget.AnyWidget):
    _esm = """
    function render({ model, el }) {
      const container = document.createElement("label");
      container.classList.add("mljar-checkbox-container");

      const input = document.createElement("input");
      input.type = "checkbox";
      input.classList.add("mljar-checkbox-input");

      const control = document.createElement("span");
      control.classList.add("mljar-checkbox-control");

      const text = document.createElement("span");
      text.classList.add("mljar-checkbox-label");

      container.appendChild(input);
      container.appendChild(control);
      container.appendChild(text);
      el.appendChild(container);

      function syncFromModel() {
        // appearance
        const a = model.get("appearance") || "toggle";
        container.classList.remove("is-toggle","is-box");
        container.classList.add(`is-${a}`);
        input.setAttribute("role", a === "toggle" ? "switch" : "checkbox");

        // value
        const v = !!model.get("value");
        if (input.checked !== v) {
          input.checked = v;
          input.setAttribute("aria-checked", String(v));
        }
        container.classList.toggle("is-checked", v);

        // disabled
        const d = !!model.get("disabled");
        input.disabled = d;
        container.classList.toggle("is-disabled", d);

        // label
        text.textContent = model.get("label") || "";

        // hidden (exists but not visible)
        container.style.display = model.get("hidden") ? "none" : "inline-flex";
      }

      input.addEventListener("change", () => {
        if (model.get("disabled")) return;

        const v = input.checked;
        if (model.get("value") !== v) {
          model.set("value", v);
          model.set("last_changed_at", new Date().toISOString());
          model.set("n_toggles", (model.get("n_toggles") || 0) + 1);
          model.save_changes();
          // model.send({ type: "changed", value: v });
        }
      });

      model.on("change:value", syncFromModel);
      model.on("change:disabled", syncFromModel);
      model.on("change:appearance", syncFromModel);
      model.on("change:label", syncFromModel);
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
      }
      */
    }
    export default { render };
    """

    _css = f"""
    .mljar-checkbox-container {{
        display: inline-flex;
        align-items: center;
        gap: 10px;
        cursor: pointer;
        user-select: none;
        -webkit-tap-highlight-color: transparent;
        font-family: {THEME.get('font_family', 'Arial, sans-serif')};
        color: {THEME.get('text_color', '#222')};
        padding-left: 5px;
    }}
    .mljar-checkbox-container.is-disabled {{
        opacity: 0.6;
        cursor: not-allowed;
    }}

    .mljar-checkbox-input {{
        position: absolute;
        opacity: 0;
        width: 0;
        height: 0;
    }}

    .mljar-checkbox-input:focus-visible + .mljar-checkbox-control {{
        box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.35);
    }}

    .mljar-checkbox-label {{
        font-size: {THEME.get('font_size', '14px')};
        line-height: 1.2;
        padding-top: 2px;
    }}

    /* --- Toggle style (15% smaller) --- */
    .mljar-checkbox-container.is-toggle .mljar-checkbox-control {{
        position: relative;
        width: 34px;
        height: 19px;
        border-radius: 999px;
        background: {THEME.get('panel_bg_hover', '#e5e7eb')};
        border: 1px solid {THEME.get('border_color', '#d0d0d0')};
        transition: background 150ms ease, border-color 150ms ease;
    }}
    .mljar-checkbox-container.is-toggle.is-checked .mljar-checkbox-control {{
        background: {THEME.get('primary_color', '#007bff')};
        border-color: {THEME.get('primary_color', '#007bff')};
    }}
    .mljar-checkbox-container.is-toggle .mljar-checkbox-control::after {{
        content: "";
        position: absolute;
        top: 2px;
        left: 2px;
        width: 15px;
        height: 15px;
        border-radius: 50%;
        background: {THEME.get('widget_background_color', '#ffffff')};
        box-shadow: 0 1px 2px rgba(0,0,0,0.12), 0 0 0 1px rgba(0,0,0,0.04);
        transition: transform 150ms ease;
    }}
    .mljar-checkbox-container.is-toggle.is-checked .mljar-checkbox-control::after {{
        transform: translateX(15px);
    }}

    /* --- Classic box style --- */
    .mljar-checkbox-container.is-box .mljar-checkbox-control {{
        width: 16px;
        height: 16px;
        border-radius: {THEME.get('border_radius_sm', '4px')};
        border: 1px solid {THEME.get('border_color', '#ccc')};
        background: {THEME.get('widget_background_color', '#fff')};
        display: inline-block;
        position: relative;
    }}
    .mljar-checkbox-container.is-box.is-checked .mljar-checkbox-control {{
        border-color: {THEME.get('primary_color', '#007bff')};
        background: {THEME.get('primary_color', '#007bff')};
    }}
    .mljar-checkbox-container.is-box.is-checked .mljar-checkbox-control::after {{
        content: "";
        position: absolute;
        left: 4px;
        top: 0px;
        width: 5px;
        height: 10px;
        border: solid #fff;
        border-width: 0 2px 2px 0;
        transform: rotate(45deg);
    }}

    .mljar-checkbox-container:not(.is-disabled):hover .mljar-checkbox-control {{
        filter: brightness(0.98);
    }}
    """

    value = traitlets.Bool(False).tag(sync=True)
    label = traitlets.Unicode("Enable").tag(sync=True)
    disabled = traitlets.Bool(False).tag(sync=True)
    hidden = traitlets.Bool(False).tag(sync=True)

    appearance = traitlets.Enum(["toggle", "box"], default_value="toggle").tag(sync=True)

    n_toggles = traitlets.Int(0).tag(sync=True)
    last_changed_at = traitlets.Unicode("").tag(sync=True)

    position = traitlets.Enum(
        values=["sidebar", "inline", "bottom"],
        default_value="sidebar",
        help="Widget placement: sidebar, inline, or bottom",
    ).tag(sync=True)

    cell_id = traitlets.Unicode(allow_none=True).tag(sync=True)

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
