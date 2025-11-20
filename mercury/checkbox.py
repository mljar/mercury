import anywidget
import traitlets
from IPython.display import display

from .manager import WidgetsManager, MERCURY_MIMETYPE
from .theme import THEME


def Checkbox(*args, key: str = "", **kwargs):
    """
    Factory that caches and reuses a CheckboxWidget instance keyed by cell code.

    Examples
    --------
    cb = Checkbox(label="Auto-refresh")               # toggle switch (default)
    cb = Checkbox(label="I agree", appearance="box")  # classic square checkbox
    """
    code_uid = WidgetsManager.get_code_uid("Checkbox", key=key, args=args, kwargs=kwargs)
    cached = WidgetsManager.get_widget(code_uid)
    if cached:
        display(cached)
        return cached
    instance = CheckboxWidget(*args, **kwargs)
    WidgetsManager.add_widget(code_uid, instance)
    display(instance)
    return instance


class CheckboxWidget(anywidget.AnyWidget):
    _esm = """
    function render({ model, el }) {
      const container = document.createElement("label");
      container.classList.add("mljar-checkbox-container");

      const appearance = model.get("appearance") || "toggle";
      container.classList.add(`is-${appearance}`);

      const input = document.createElement("input");
      input.type = "checkbox";
      input.checked = !!model.get("value");
      input.disabled = !!model.get("disabled");
      input.classList.add("mljar-checkbox-input");
      input.setAttribute("aria-checked", String(input.checked));
      input.setAttribute("role", appearance === "toggle" ? "switch" : "checkbox");

      const control = document.createElement("span");
      control.classList.add("mljar-checkbox-control");

      const text = document.createElement("span");
      text.classList.add("mljar-checkbox-label");
      text.textContent = model.get("label") || "";

      container.appendChild(input);
      container.appendChild(control);
      container.appendChild(text);
      el.appendChild(container);

      function syncFromModel() {
        const v = !!model.get("value");
        if (input.checked !== v) {
          input.checked = v;
          input.setAttribute("aria-checked", String(v));
        }
        container.classList.toggle("is-checked", v);
      }
      function syncDisabled() {
        const d = !!model.get("disabled");
        input.disabled = d;
        container.classList.toggle("is-disabled", d);
      }
      function syncAppearance() {
        const a = model.get("appearance") || "toggle";
        container.classList.remove("is-toggle","is-box");
        container.classList.add(`is-${a}`);
        input.setAttribute("role", a === "toggle" ? "switch" : "checkbox");
      }
      function syncLabel() {
        text.textContent = model.get("label") || "";
      }

      input.addEventListener("change", () => {
        const v = input.checked;
        if (model.get("value") !== v) {
          model.set("value", v);
          model.set("last_changed_at", new Date().toISOString());
          model.set("n_toggles", (model.get("n_toggles") || 0) + 1);
          model.save_changes();
          model.send({ type: "changed", value: v });
        }
      });

      model.on("change:value", syncFromModel);
      model.on("change:disabled", syncDisabled);
      model.on("change:appearance", syncAppearance);
      model.on("change:label", syncLabel);

      syncFromModel();
      syncDisabled();
      syncAppearance();
      syncLabel();

      const css = model.get("custom_css");
      if (css && css.trim().length > 0) {
        const styleTag = document.createElement("style");
        styleTag.textContent = css;
        el.appendChild(styleTag);
      }

      // ---- read cell id ----
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
        width: 34px;  /* smaller */
        height: 19px; /* smaller */
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
        width: 15px;   /* smaller thumb */
        height: 15px;
        border-radius: 50%;
        background: {THEME.get('widget_background_color', '#ffffff')};
        box-shadow: 0 1px 2px rgba(0,0,0,0.12), 0 0 0 1px rgba(0,0,0,0.04);
        transition: transform 150ms ease;
    }}
    .mljar-checkbox-container.is-toggle.is-checked .mljar-checkbox-control::after {{
        transform: translateX(15px);  /* adjusted distance */
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
    appearance = traitlets.Enum(["toggle", "box"], default_value="toggle").tag(sync=True)
    n_toggles = traitlets.Int(0).tag(sync=True)
    last_changed_at = traitlets.Unicode("").tag(sync=True)
    custom_css = traitlets.Unicode(default_value="", help="Extra CSS appended after default styles").tag(sync=True)
    position = traitlets.Enum(["sidebar", "inline", "bottom"], default_value="sidebar").tag(sync=True)
    cell_id = traitlets.Unicode(allow_none=True).tag(sync=True)

    def _repr_mimebundle_(self, **kwargs):
        data = super()._repr_mimebundle_(**kwargs)
        if len(data) > 1:
            mercury_mime = {
                "widget": type(self).__qualname__,
                "model_id": self.model_id,
                "position": self.position,
            }
            import json
            data[0][MERCURY_MIMETYPE] = mercury_mime
        return data
