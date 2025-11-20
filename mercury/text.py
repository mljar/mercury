import anywidget
import traitlets

from .manager import WidgetsManager, MERCURY_MIMETYPE
from .theme import THEME

def TextInput(*args, key="", **kwargs):
    code_uid = WidgetsManager.get_code_uid("TextInput", key=key, args=args, kwargs=kwargs)
    cached = WidgetsManager.get_widget(code_uid)
    if cached:
        display(cached)
        return cached
    instance = TextInputWidget(*args, **kwargs)
    WidgetsManager.add_widget(code_uid, instance)
    display(instance)
    return instance

class TextInputWidget(anywidget.AnyWidget):
    _esm = """
    function render({ model, el }) {
      // Container
      let container = document.createElement("div");
      container.classList.add("mljar-textinput-container");

      // Label
      let topLabel = document.createElement("div");
      topLabel.classList.add("mljar-textinput-top-label");
      topLabel.innerHTML = model.get("label") || "Enter text";

      // Input
      let input = document.createElement("input");
      input.type = "text";
      input.value = model.get("value");
      input.classList.add("mljar-textinput-input");

      let debounceTimer = null;
      input.addEventListener("input", () => {
        model.set("value", input.value);
        if (debounceTimer) clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => model.save_changes(), 100);
      });

      model.on("change:value", () => {
        input.value = model.get("value");
      });

      // Build
      container.appendChild(topLabel);
      container.appendChild(input);
      el.appendChild(container);

      const css = model.get("custom_css");
      if (css && css.trim().length > 0) {
        let styleTag = document.createElement("style");
        styleTag.textContent = css;
        el.appendChild(styleTag);
      }

      // ---- read cell id (no DOM modifications) ----
      const ID_ATTR = 'data-cell-id';
      const hostWithId = el.closest(`[${ID_ATTR}]`);
      const cellId = hostWithId ? hostWithId.getAttribute(ID_ATTR) : null;

      if (cellId) {
        model.set('cell_id', cellId);
        model.save_changes();
        model.send({ type: 'cell_id_detected', value: cellId });
      } else {
        // handle case where the attribute appears slightly later
        const mo = new MutationObserver(() => {
          const host = el.closest(`[${ID_ATTR}]`);
          const newId = host?.getAttribute(ID_ATTR);
          if (newId) {
            model.set('cell_id', newId);
            model.save_changes();
            model.send({ type: 'cell_id_detected', value: newId });
            mo.disconnect();
          }
        });
        mo.observe(document.body, { attributes: true, subtree: true, attributeFilter: [ID_ATTR] });
      }
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
        font-weight: {THEME.get('font_weight', 'bold')};
        color: {THEME.get('text_color', '#222')};

    }}

    .mljar-textinput-top-label {{
        margin-bottom: 6px;
        text-align: left;
        width: 100%;
        font-weight: bold;
    }}

    .mljar-textinput-input {{
        width: 100%;
        border: { '1px solid ' + THEME.get('border_color', '#ccc') if THEME.get('border_visible', True) else 'none'};
        border-radius: {THEME.get('border_radius', '6px')};
        padding: 6px 10px;
        min-height: 1.6em;
        box-sizing: border-box;
        background: {THEME.get('widget_background_color', '#fff')};
        color: {THEME.get('text_color', '#222')};
    }}

    .mljar-textinput-input:focus {{
        outline: none;
        border-color: {THEME.get('primary_color', '#007bff')};
    }}
    """


    value = traitlets.Unicode("").tag(sync=True)
    label = traitlets.Unicode("Enter text").tag(sync=True)
    custom_css = traitlets.Unicode(default_value="", help="Extra CSS to append to default styles").tag(sync=True)
    position = traitlets.Enum(
        values=["sidebar", "inline", "bottom"],
        default_value="sidebar",
        help="Widget placement: sidebar, inline, or bottom"
    ).tag(sync=True)
    cell_id = traitlets.Unicode(allow_none=True).tag(sync=True) 

    def _repr_mimebundle_(self, **kwargs):
        data = super()._repr_mimebundle_()
        if len(data) > 1:
            mercury_mime = {
                "widget": type(self).__qualname__,
                "model_id": self.model_id,
                "position": self.position
            }
            import json
            data[0][MERCURY_MIMETYPE] = mercury_mime
        return data
