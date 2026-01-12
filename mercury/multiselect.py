# Copyright MLJAR Sp. z o.o.
# Licensed under the Apache License, Version 2.0 (Apache-2.0)

import warnings
from typing import List, Literal

import anywidget
import traitlets
from IPython.display import display

from .manager import MERCURY_MIMETYPE, WidgetsManager
from .theme import THEME

Position = Literal["sidebar", "inline", "bottom"]


def MultiSelect(
    label: str = "Select",
    value: List[str] | None = None,
    choices: List[str] = [],
    placeholder: str = "",
    position: Position = "sidebar",
    disabled: bool = False,
    hidden: bool = False,
    key: str = "",
):
    """
    Create and display a MultiSelect widget.

    This function instantiates a `MultiSelectWidget` with the given label,
    initial selected values, and list of choices. If a widget with the same
    configuration (identified by a unique code UID generated from widget type,
    arguments, and keyword arguments) already exists in the `WidgetsManager`,
    the existing instance is returned and displayed instead of creating a new one.

    Parameters
    ----------
    label : str
        Human-readable label shown next to the widget.
        The default is `"Select"`.
    value : list[str] or None
        Initial list of selected values. If `None` or empty, the first element
        from `choices` is selected by default.
    choices : list[str]
        Options available for selection. Must be non-empty.
    placeholder : str
        Text shown when no values are selected.
    position : {"sidebar", "inline", "bottom"}, optional
        Controls where the widget is displayed:
        - `"sidebar"` — left sidebar panel (default).
        - `"inline"` — rendered in the notebook flow.
        - `"bottom"` — rendered after all notebook cells.
    disabled : bool, optional
        If `True`, the widget is rendered but cannot be interacted with.
    hidden : bool, optional
        If `True`, the widget exists but is not visible in the UI.
    key : str, optional
        Unique identifier used to differentiate widgets with the same parameters.

    Returns
    -------
    MultiSelectWidget
        The created or retrieved MultiSelect widget instance.

    Examples
    --------
    Basic usage:

    >>> from mercury import MultiSelect
    >>> fruits = MultiSelect(
    ...     label="Choose fruits",
    ...     choices=["Apple", "Banana", "Cherry"],
    ... )

    Now the widget appears in the UI. To see the selected values:

    >>> fruits.value
    ['Apple']

    After a user changes the selection in the UI:

    >>> fruits.value
    ['Banana', 'Cherry']

    The value is always a list of the currently selected options.
    """
    if len(choices) == 0:
        raise Exception("Please provide choices list. God bless you <3")

    # Normalize incoming value
    if value is None:
        value = [choices[0]]
    else:
        # Ensure list and filter invalid values
        if not isinstance(value, list):
            value = [str(value)]
        invalid = [v for v in value if v not in choices]
        if invalid:
            warnings.warn(
                "\nSome values are not included in choices. "
                "Automatically removed invalid values and ensured at least "
                "one valid selection (first element from choices if needed)."
            )
        value = [v for v in value if v in choices]
        if len(value) == 0:
            value = [choices[0]]

    args = [label, choices, placeholder, position]
    kwargs = {
        "label": label, 
        "choices": choices,
        "placeholder": placeholder,
        "position": position
    }

    code_uid = WidgetsManager.get_code_uid("MultiSelect", key=key, args=args, kwargs=kwargs)
    cached = WidgetsManager.get_widget(code_uid)
    if cached:
        display(cached)
        return cached

    instance = MultiSelectWidget(**kwargs)
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

      // ---- read cell id (no DOM modifications) ----
      /*const ID_ATTR = 'data-cell-id';
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
      */
    }
    export default { render };
    """

    # minimal CSS
    _css = f"""
    .mljar-ms-container {{
      display: flex;
      flex-direction: column;
      font-family: {THEME.get('font_family', 'Arial, sans-serif')};
      font-size: {THEME.get('font_size', '14px')};
      margin-bottom: 8px;
      padding-left: 4px;
      padding-right: 4px;
    }}

    .mljar-ms-label {{
      margin-bottom: 4px;
      font-weight: 600;
      color: {THEME.get('text_color', '#222')};
    }}

    .mljar-ms-control {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      border: 1px solid {THEME.get('border_color', '#ccc')};
      border-radius: {THEME.get('border_radius', '6px')};
      padding: 4px 6px;
      background: #fff;
      box-sizing: border-box;
      cursor: pointer;
      gap: 6px;
    }}

    .mljar-ms-chips {{
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
      flex: 1 1 auto;
      min-height: 20px;
    }}

    .mljar-ms-placeholder {{
      color: #888;
      white-space: nowrap;
    }}

    .mljar-ms-chip {{
      background: #e9ecef;
      padding: 2px 6px;
      border-radius: 999px;
      display: inline-flex;
      align-items: center;
      gap: 4px;
      max-width: 100%;
      font-size: 12px;
    }}

    .mljar-ms-chip-x {{
      border: none;
      background: transparent;
      cursor: pointer;
      font-size: 11px;
      line-height: 1;
      padding: 0;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      opacity: 0.7;
      color: {THEME.get('text_color', '#222')};
    }}

    .mljar-ms-chip-x:hover {{
      opacity: 1;
    }}

    .mljar-ms-actions {{
      display: inline-flex;
      align-items: center;
      gap: 4px;
      flex-shrink: 0;
    }}

    .mljar-ms-btn {{
      border: none;
      background: transparent;
      cursor: pointer;
      padding: 2px 6px;
      border-radius: 999px;
      font-size: 11px;
      line-height: 1;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      color: {THEME.get('text_color', '#222')};
      opacity: 0.7;
      transition: background 0.15s ease, opacity 0.15s ease, transform 0.08s ease;
    }}

    .mljar-ms-btn:hover {{
      background: #f1f3f5;
      opacity: 1;
    }}

    .mljar-ms-btn:active {{
      transform: translateY(1px);
    }}

    .mljar-ms-btn:disabled,
    .mljar-ms-btn[disabled] {{
      cursor: default;
      opacity: 0.4;
      background: transparent;
      transform: none;
    }}

    .mljar-ms-dropdown {{
      display: none;
      border: 1px solid {THEME.get('border_color', '#ccc')};
      border-radius: {THEME.get('border_radius', '6px')};
      margin-top: 4px;
      background: #fff;
      box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
      box-sizing: border-box;
      max-height: 180px;
      overflow: hidden;
    }}

    .mljar-ms-list {{
      list-style: none;
      margin: 0;
      padding: 4px 0;
      max-height: 180px;
      overflow: auto;
    }}

    .mljar-ms-item {{
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 4px 8px;
      cursor: pointer;
      font-size: 13px;
    }}

    .mljar-ms-item:hover {{
      background: #f6f6f6;
    }}

    .mljar-ms-item input[type="checkbox"] {{
      appearance: none;
      -webkit-appearance: none;
      margin: 0;
      width: 14px;
      height: 14px;
      border: 1px solid #444;
      border-radius: 3px; 
      background: #fff; 
      cursor: pointer;
      display: inline-block;
      position: relative;
    }}
 
    .mljar-ms-item input[type="checkbox"]:checked {{
      background: #228be6; 
      border-color: #228be6;
    }}
 
    .mljar-ms-item input[type="checkbox"]:checked::after {{
      content: "";
      position: absolute;
      top: 0px;
      left: 3px;
      width: 4px;
      height: 8px;
      border: solid white;
      border-width: 0 2px 2px 0;
      transform: rotate(45deg);
    }}
    """

    value = traitlets.List(traitlets.Unicode(), default_value=[]).tag(sync=True)
    choices = traitlets.List(traitlets.Unicode(), default_value=[]).tag(sync=True)
    label = traitlets.Unicode(default_value="Select").tag(sync=True)
    placeholder = traitlets.Unicode(default_value="").tag(sync=True)
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
