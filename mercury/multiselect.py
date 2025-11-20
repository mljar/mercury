import anywidget
import traitlets
import json
# from IPython.display import display
from .manager import WidgetsManager, MERCURY_MIMETYPE
from .theme import THEME


def MultiSelect(*args, key: str = "", **kwargs):
    code_uid = WidgetsManager.get_code_uid("MultiSelect", key=key, args=args, kwargs=kwargs)
    cached = WidgetsManager.get_widget(code_uid)
    if cached:
        display(cached)
        return cached
    instance = MultiSelectWidget(*args, **kwargs)
    WidgetsManager.add_widget(code_uid, instance)
    display(instance)
    return instance


class MultiSelectWidget(anywidget.AnyWidget):
    _esm = """
    function render({ model, el }) {
      const getSelected = () => Array.isArray(model.get("value")) ? [...model.get("value")] : [];
      const getChoices  = () => Array.isArray(model.get("choices")) ? [...model.get("choices")] : [];
      const isDisabled  = () => !!model.get("disabled");
      const setModelValueDebounced = (() => {
        let t = null;
        return (val) => {
          model.set("value", val);
          if (t) clearTimeout(t);
          t = setTimeout(() => model.save_changes(), 100);
        };
      })();

      const container = document.createElement("div");
      container.classList.add("mljar-ms-container");

      const labelText = model.get("label");
      if (labelText) {
        const topLabel = document.createElement("div");
        topLabel.classList.add("mljar-ms-label");
        topLabel.innerHTML = labelText;
        container.appendChild(topLabel);
      }

      const control = document.createElement("div");
      control.classList.add("mljar-ms-control");

      const chipsWrap = document.createElement("div");
      chipsWrap.classList.add("mljar-ms-chips");

      const actions = document.createElement("div");
      actions.classList.add("mljar-ms-actions");

      const clearBtn = document.createElement("button");
      clearBtn.classList.add("mljar-ms-btn");
      clearBtn.innerHTML = "&times;";

      const toggleBtn = document.createElement("button");
      toggleBtn.classList.add("mljar-ms-btn");
      toggleBtn.innerHTML = "&#9662;";

      actions.appendChild(clearBtn);
      actions.appendChild(toggleBtn);

      control.appendChild(chipsWrap);
      control.appendChild(actions);

      const dropdown = document.createElement("div");
      dropdown.classList.add("mljar-ms-dropdown");
      const list = document.createElement("ul");
      list.classList.add("mljar-ms-list");
      dropdown.appendChild(list);

      container.appendChild(control);
      container.appendChild(dropdown);
      el.appendChild(container);

      let open = false;

      function renderChips() {
        const selected = getSelected();
        chipsWrap.innerHTML = "";
        if (selected.length === 0) {
          const ph = document.createElement("span");
          ph.classList.add("mljar-ms-placeholder");
          ph.textContent = model.get("placeholder") || "";
          chipsWrap.appendChild(ph);
        } else {
          selected.forEach(val => {
            const chip = document.createElement("span");
            chip.classList.add("mljar-ms-chip");
            chip.textContent = val;
            const x = document.createElement("button");
            x.classList.add("mljar-ms-chip-x");
            x.innerHTML = "&times;";
            x.addEventListener("click", (e) => {
              e.stopPropagation();
              if (isDisabled()) return;
              const newSel = getSelected().filter(v => v !== val);
              setModelValueDebounced(newSel);
            });
            chip.appendChild(x);
            chipsWrap.appendChild(chip);
          });
        }
        clearBtn.disabled = isDisabled() || getSelected().length === 0;
      }

      function renderOptions() {
        const choices = getChoices();
        const selected = new Set(getSelected());
        list.innerHTML = "";
        choices.forEach(val => {
          const li = document.createElement("li");
          li.classList.add("mljar-ms-item");
          const cb = document.createElement("input");
          cb.type = "checkbox";
          cb.checked = selected.has(val);
          cb.disabled = isDisabled();
          const lbl = document.createElement("span");
          lbl.textContent = val;
          li.appendChild(cb);
          li.appendChild(lbl);
          li.addEventListener("click", (e) => {
            e.stopPropagation();
            if (isDisabled()) return;
            const sel = new Set(getSelected());
            if (sel.has(val)) sel.delete(val);
            else sel.add(val);
            setModelValueDebounced([...sel]);
          });
          list.appendChild(li);
        });
      }

      function setOpen(next) {
        open = !!next;
        dropdown.style.display = open ? "block" : "none";
      }

      control.addEventListener("click", () => {
        if (isDisabled()) return;
        setOpen(!open);
      });
      toggleBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        if (isDisabled()) return;
        setOpen(!open);
      });
      clearBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        if (isDisabled()) return;
        setModelValueDebounced([]);
      });

      document.addEventListener("click", (e) => {
        if (!el.contains(e.target)) setOpen(false);
      });

      renderChips();
      renderOptions();
      setOpen(false);

      model.on("change:value", () => {
        renderChips();
        renderOptions();
      });
      model.on("change:choices", () => {
        renderChips();
        renderOptions();
      });
      model.on("change:disabled", () => {
        clearBtn.disabled = isDisabled() || getSelected().length === 0;
        setOpen(false);
      });

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

    # minimal CSS
    _css = f"""
    .mljar-ms-container {{
      display: flex;
      flex-direction: column;
      width: 100%;
      font-family: {THEME.get('font_family', 'Arial, sans-serif')};
      font-size: {THEME.get('font_size', '14px')};
      margin-bottom: 8px;
    }}
    .mljar-ms-label {{
      margin-bottom: 4px;
      font-weight: bold;
    }}
    .mljar-ms-control {{
      display: flex;
      justify-content: space-between;
      border: 1px solid {THEME.get('border_color', '#ccc')};
      border-radius: {THEME.get('border_radius', '6px')};
      padding: 4px;
      background: #fff;
      cursor: pointer;
    }}
    .mljar-ms-chips {{
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
    }}
    .mljar-ms-placeholder {{
      color: #888;
    }}
    .mljar-ms-chip {{
      background: #e9ecef;
      padding: 2px 6px;
      border-radius: 10px;
    }}
    .mljar-ms-chip-x {{
      border: none;
      background: transparent;
      cursor: pointer;
    }}
    .mljar-ms-dropdown {{
      display: none;
      border: 1px solid {THEME.get('border_color', '#ccc')};
      border-radius: {THEME.get('border_radius', '6px')};
      margin-top: 4px;
      background: #fff;
    }}
    .mljar-ms-list {{
      list-style: none;
      margin: 0;
      padding: 0;
      max-height: 150px;
      overflow: auto;
    }}
    .mljar-ms-item {{
      display: flex;
      gap: 6px;
      padding: 4px;
      cursor: pointer;
    }}
    .mljar-ms-item:hover {{
      background: #f6f6f6;
    }}
    """

    value = traitlets.List(traitlets.Unicode(), default_value=[]).tag(sync=True)
    choices = traitlets.List(traitlets.Unicode(), default_value=[]).tag(sync=True)
    label = traitlets.Unicode(default_value="Select options").tag(sync=True)
    placeholder = traitlets.Unicode(default_value="").tag(sync=True)
    disabled = traitlets.Bool(default_value=False).tag(sync=True)
    hidden = traitlets.Bool(default_value=False).tag(sync=True)
    custom_css = traitlets.Unicode(default_value="", help="Extra CSS").tag(sync=True)
    position = traitlets.Enum(
        values=["sidebar", "inline", "bottom"],
        default_value="sidebar",
        help="Widget placement: sidebar, inline, or bottom",
    ).tag(sync=True)
    cell_id = traitlets.Unicode(allow_none=True).tag(sync=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not isinstance(self.value, list):
            self.value = []
        self.value = [v for v in self.value if v in self.choices]
        if len(self.value) == 0 and len(self.choices) > 0:
            self.value = [self.choices[0]]

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
