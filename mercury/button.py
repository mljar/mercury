import anywidget
import traitlets
from IPython.display import display

from .manager import WidgetsManager, MERCURY_MIMETYPE
from .theme import THEME


def Button(*args, key: str = "", **kwargs):
    """
    Factory that caches and reuses a ButtonWidget instance keyed by cell code.
    Usage:
        btn = Button(label="Run", variant="primary", size="md")
    """
    code_uid = WidgetsManager.get_code_uid("Button", key=key, args=args, kwargs=kwargs)
    cached = WidgetsManager.get_widget(code_uid)
    if cached:
        display(cached)
        return cached
    instance = ButtonWidget(*args, **kwargs)
    WidgetsManager.add_widget(code_uid, instance)
    display(instance)
    return instance


class ButtonWidget(anywidget.AnyWidget):
    _esm = """
    function render({ model, el }) {
      const container = document.createElement("div");
      container.classList.add("mljar-button-container");

      const btn = document.createElement("button");
      btn.classList.add("mljar-button");

      const variant = model.get("variant") || "primary";
      const size = model.get("size") || "md";
      btn.classList.add(`is-${variant}`, `is-${size}`);
      btn.disabled = !!model.get("disabled");
      btn.textContent = model.get("label") || "Run";

      btn.addEventListener("click", () => {
        const current = model.get("n_clicks") || 0;
        model.set("n_clicks", current + 1);
        model.set("last_clicked_at", new Date().toISOString());
        model.set("value", true);  // ✅ set value=True on click
        model.save_changes();
        model.send({ type: "clicked", n_clicks: current + 1 });
      });

      // Reactivity
      model.on("change:label", () => { btn.textContent = model.get("label"); });
      model.on("change:variant", () => {
        ["is-primary","is-secondary","is-outline","is-danger"].forEach(c => btn.classList.remove(c));
        btn.classList.add(`is-${model.get("variant")}`);
      });
      model.on("change:size", () => {
        ["is-sm","is-md","is-lg"].forEach(c => btn.classList.remove(c));
        btn.classList.add(`is-${model.get("size")}`);
      });
      model.on("change:disabled", () => { btn.disabled = !!model.get("disabled"); });

      container.appendChild(btn);
      el.appendChild(container);

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
    .mljar-button-container {{
        display: inline-flex;
        width: auto;
        font-family: {THEME.get('font_family', 'Arial, sans-serif')};
    }}

    .mljar-button {{
        border: 1px solid {THEME.get('border_color', '#d0d0d0')};
        background: {THEME.get('widget_background_color', '#ffffff')};
        color: {THEME.get('text_color', '#222')};
        border-radius: {THEME.get('border_radius', '8px')};
        padding: 4px 12px 4px 12px;  
        margin-top: 5px;
        margin-bottom: 5px;
        cursor: pointer;
        transition: transform 120ms ease, box-shadow 120ms ease, background 120ms ease, border-color 120ms ease;
        user-select: none;
        outline: none;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        font-size: {THEME.get('font_size', '14px')};
        font-weight: {THEME.get('font_weight', '600')};
        box-shadow: {THEME.get('button_shadow', '0 1px 2px rgba(0,0,0,0.06)')};
    }}

    .mljar-button:hover:not(:disabled) {{
        transform: translateY(-1px);
        box-shadow: {THEME.get('button_shadow_hover', '0 2px 6px rgba(0,0,0,0.08)')};
        border-color: {THEME.get('primary_color', '#007bff')};
    }}

    .mljar-button:active:not(:disabled) {{
        transform: translateY(0);
        box-shadow: {THEME.get('button_shadow', '0 1px 2px rgba(0,0,0,0.06)')};
    }}

    .mljar-button:disabled {{
        opacity: 0.6;
        cursor: not-allowed;
    }}

    /* Variants */
    .mljar-button.is-primary {{
        background: {THEME.get('primary_color', '#007bff')};
        color: {THEME.get('button_primary_text', '#fff')};
        border-color: {THEME.get('primary_color', '#007bff')};
    }}
    .mljar-button.is-primary:hover:not(:disabled) {{
        filter: brightness(0.98);
    }}

    .mljar-button.is-secondary {{
        background: {THEME.get('panel_bg', '#f7f7fa')};
        color: {THEME.get('text_color', '#222')};
    }}

    .mljar-button.is-outline {{
        background: transparent;
        color: {THEME.get('primary_color', '#007bff')};
        border: 1px solid {THEME.get('primary_color', '#007bff')};
    }}
    .mljar-button.is-outline:hover:not(:disabled) {{
        background: {THEME.get('primary_color', '#007bff')};
        color: #fff;
    }}

    .mljar-button.is-danger {{
        background: {THEME.get('danger_color', '#dc3545')};
        color: #fff;
        border-color: {THEME.get('danger_color', '#dc3545')};
    }}

    /* Sizes */
    .mljar-button.is-sm {{
        padding: 3px 10px 3px 10px;
        font-size: 12px;
        border-radius: {THEME.get('border_radius_sm', '2px')};
    }}
    .mljar-button.is-md {{
        padding: 4px 12px 4px 12px;  
    }}
    .mljar-button.is-lg {{
        padding: 8px 16px 8px 16px;
        font-size: 16px;
        border-radius: {THEME.get('border_radius_lg', '4px')};
    }}
    """

    # --- Backend synced traits ---
    label = traitlets.Unicode("Run").tag(sync=True)
    variant = traitlets.Enum(["primary", "secondary", "outline", "danger"], default_value="primary").tag(sync=True)
    size = traitlets.Enum(["sm", "md", "lg"], default_value="md").tag(sync=True)
    disabled = traitlets.Bool(False).tag(sync=True)

    # "value" traitlet (True after click)
    value = traitlets.Bool(False).tag(sync=True)

    n_clicks = traitlets.Int(0).tag(sync=True)
    last_clicked_at = traitlets.Unicode("").tag(sync=True)

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
            data[0][MERCURY_MIMETYPE] = mercury_mime
        return data
