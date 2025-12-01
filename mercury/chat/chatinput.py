import anywidget
import traitlets
from IPython.display import display

from ..manager import WidgetsManager, MERCURY_MIMETYPE
from ..theme import THEME

def ChatInput(*args, key="", **kwargs):
    code_uid = WidgetsManager.get_code_uid("ChatInput", key=key, args=args, kwargs=kwargs)
    cached = WidgetsManager.get_widget(code_uid)
    if cached:
        display(cached)
        return cached
    instance = ChatInputWidget(*args, **kwargs)
    WidgetsManager.add_widget(code_uid, instance)
    display(instance)
    return instance


class ChatInputWidget(anywidget.AnyWidget):
    """
    Public traits:
      - value: last submitted text (updates only on submit)
      - placeholder, button_icon, send_on_enter, position, custom_css, cell_id

    Internal-ish trigger:
      - submitted: message sent (synced), underscore-prefixed to signal non-public API.
    """

    _esm = """
    function render({ model, el }) {
      el.style.flex = "0 0 auto";
      const container = document.createElement("div");
      container.classList.add("mljar-chatinput-container");

      const input = document.createElement("input");
      input.type = "text";
      input.placeholder = model.get("placeholder") || "Type a message...";
      input.value = model.get("value") || "";
      input.classList.add("mljar-chatinput-input");

      const btn = document.createElement("button");
      btn.type = "button";
      btn.classList.add("mljar-chatinput-button");
      btn.textContent = model.get("button_icon") || "➤";
      btn.setAttribute("aria-label", "Send message");

      container.appendChild(input);
      container.appendChild(btn);
      el.appendChild(container);

      // Keep input in sync if Python changes 'value' (e.g., programmatic set/restore)
      model.on("change:value", () => {
        const newVal = model.get("value") ?? "";
        if (input.value !== newVal) input.value = newVal;
      });

      // Submit logic: update submitted and value ONLY here
      const sendMessage = () => {
        const msg = (input.value || "").trim();
        if (!msg) return;

        // Signal to kernel
        model.set("submitted", msg);

        // Update public 'value' ONLY at submit time
        model.set("value", msg);

        // Clear visible input (does NOT touch model 'value')
        input.value = "";

        // Persist once
        model.save_changes();
      };

      btn.addEventListener("click", sendMessage);

      input.addEventListener("keydown", (ev) => {
        const sendOnEnter = !!model.get("send_on_enter");
        if (!sendOnEnter) return;
        if (ev.key === "Enter" && !ev.shiftKey) {
          ev.preventDefault();
          sendMessage();
        }
      });

      // Custom CSS hook
      const css = model.get("custom_css");
      if (css && css.trim().length > 0) {
        const styleTag = document.createElement("style");
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
    .mljar-chatinput-container {{
        display: flex;
        flex-direction: row;
        align-items: center;
        width: 100%;
        min-width: 160px;
        box-sizing: border-box;
        gap: 8px;
        font-family: {THEME.get('font_family', 'Arial, sans-serif')};
        font-size: {THEME.get('font_size', '14px')};
        color: {THEME.get('text_color', '#222')};
        padding-top: 5px;
        padding-bottom: 5px;
    }}

    .mljar-chatinput-input {{
        flex: 1 1 auto;
        width: 100%;
        border: { '1px solid ' + THEME.get('border_color', '#ccc') if THEME.get('border_visible', True) else 'none'};
        border-radius: {THEME.get('border_radius', '6px')};
        padding: 6px 10px;
        min-height: 1.6em;
        background: {THEME.get('widget_background_color', '#fff')};
        color: {THEME.get('text_color', '#222')};
        box-sizing: border-box;
    }}
    .mljar-chatinput-input:focus {{
        outline: none;
        border-color: {THEME.get('primary_color', '#007bff')};
    }}

    .mljar-chatinput-button {{
        flex: 0 0 auto;
        border: none;
        border-radius: {THEME.get('border_radius', '6px')};
        padding: 6px 12px;
        min-height: 1.6em;
        cursor: pointer;
        background: {THEME.get('primary_color', '#007bff')};
        color: {THEME.get('button_text_color', '#fff')};
        font-weight: bold;
    }}
    .mljar-chatinput-button:hover {{
        filter: brightness(0.95);
    }}
    """

    # Public traits
    value = traitlets.Unicode("").tag(sync=True)  # last submitted
    placeholder = traitlets.Unicode("Type a message...").tag(sync=True)
    button_icon = traitlets.Unicode("➤").tag(sync=True)
    send_on_enter = traitlets.Bool(True).tag(sync=True)

    custom_css = traitlets.Unicode(
        default_value="", help="Extra CSS to append to default styles"
    ).tag(sync=True)

    position = traitlets.Enum(
        values=["sidebar", "inline", "bottom"],
        default_value="bottom",
        help="Widget placement: sidebar, inline, or bottom",
    ).tag(sync=True)

    # NEW: synced cell id
    cell_id = traitlets.Unicode(allow_none=True).tag(sync=True)

    # Internal-ish trigger (still syncs, but looks private)
    submitted = traitlets.Unicode("").tag(sync=True)

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
