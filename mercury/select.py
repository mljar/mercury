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

def Select(
    label: str = "Select",
    value: str = "",
    choices: List[str] = [],
    position: Position = "sidebar",
    disabled: bool = False,
    hidden: bool = False,
    key: str = ""
):
    """
    Create and display a Select widget.

    This function instantiates a `SelectWidget` with the given label,
    initial value, and list of choices. If a widget with the same
    configuration (identified by a unique code UID generated from
    widget type, arguments, and keyword arguments) already exists in
    the `WidgetsManager`, the existing instance is returned and
    displayed instead of creating a new one.

    Parameters
    ----------
    label : str
        Human-readable label shown next to the widget.
        The default is `"Select"`.
    value : str
        The initial selected value in the dropdown. 
        The default is `""`.
    choices : list[str]
        Options available for selection.
        The default is `[]`.
    position : {"sidebar", "inline", "bottom"}, optional
        Controls where the widget is displayed:

        - `"sidebar"` — place the widget in the left sidebar panel (default).
        - `"inline"` — render the widget directly in the notebook flow
          (where the code cell is executed).
        - `"bottom"` — render the widget after all notebook cells.
    disabled : bool, optional
        If `True`, the widget is rendered but cannot be interacted with. 
    hidden : bool, optional
        If `True`, the widget exists but is not visible in the UI. 
    key : str, optional
        Unique identifier used to differentiate widgets with the same parameters.

    Returns
    -------
    SelectWidget
        The created or retrieved Select widget instance.

    Examples
    --------
    Basic usage:

    >>> from mercury import Select
    >>> fruit = Select(
    ...     label="Choose fruit",
    ...     choices=["Apple", "Banana", "Cherry"]
    ... )

    Now the widget appears in the UI. To display the current value:

    >>> fruit.value
    'Apple'

    After a user changes the selection in the UI:

    >>> fruit.value
    'Banana'

    The value always reflects the latest selection chosen by the user.
    """

    if len(choices) == 0:
        raise Exception("Please provide choices list. God bless you <3")

    if value == "":
        value = choices[0]
    
    if value not in choices:
        value = choices[0]
        warnings.warn("\nYour value is not included in choices. Automatically set value to first element from choices.")

    args = [label, choices, position]
    kwargs = {
        "label": label,
        "choices": choices,
        "position": position
    }

    code_uid = WidgetsManager.get_code_uid("Select", key=key, args=args, kwargs=kwargs)
    cached = WidgetsManager.get_widget(code_uid)
    if cached:
        display(cached)
        return cached

    instance = SelectWidget(**kwargs)
    WidgetsManager.add_widget(code_uid, instance)
    display(instance)
    return instance



class SelectWidget(anywidget.AnyWidget):
    _esm = """
    function render({ model, el }) {
      let container = document.createElement("div");
      container.classList.add("mljar-select-container");

      if (model.get("label")) {
        let topLabel = document.createElement("div");
        topLabel.classList.add("mljar-select-label");
        topLabel.innerHTML = model.get("label");
        container.appendChild(topLabel);
      }

      let select = document.createElement("select");
      select.classList.add("mljar-select-widget-input");

      if (model.get("disabled")) {
        select.disabled = true;
      }

      const choices = model.get("choices") || [];
      const currentValue = model.get("value");

      choices.forEach(choice => {
        let option = document.createElement("option");
        option.value = choice;
        option.innerHTML = choice;
        if (choice === currentValue) {
          option.selected = true;
        }
        select.appendChild(option);
      });

      let debounceTimer = null;
      select.addEventListener("change", () => {
        const val = select.value;
        model.set("value", val);
        if (debounceTimer) clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            model.save_changes();
        }, 100);
      });

      model.on("change:value", () => {
        select.value = model.get("value");
      });

      container.appendChild(select);
      el.appendChild(container);

      // ---- read cell id (no DOM modifications) ----
      /*
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
      */
    }
    export default { render };
    """

    # simplified CSS
    _css = f"""
    .mljar-select-container {{
      display: flex;
      flex-direction: column;
      font-family: {THEME.get('font_family', 'Arial, sans-serif')};
      font-size: {THEME.get('font_size', '14px')};
      color: {THEME.get('text_color', '#222')};
      margin-bottom: 8px;
      padding-left: 4px;
      padding-right: 4px;
    }}

    .mljar-select-label {{
      margin-bottom: 4px;
      font-weight: 600;
    }}

    .mljar-select-widget-input {{
      width: 100%;
      padding: 6px;
      border: 1px solid {THEME.get('border_color', '#ccc')};
      border-radius: {THEME.get('border_radius', '6px')};
      background: #fff;
      box-sizing: border-box;
      
      appearance: none !important;
      background-color: #ffffff !important;
      color: {THEME.get('text_color', '#222')} !important; 
    }}

    .mljar-select-widget-input:disabled {{
      background: #f5f5f5;
      color: #888;
      cursor: not-allowed;
    }}
    """

    value = traitlets.Unicode(default_value="").tag(sync=True)
    choices = traitlets.List(traitlets.Unicode(), default_value=[]).tag(sync=True)
    label = traitlets.Unicode(default_value="Select").tag(sync=True)
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
        # default value -> first element of choices
        if (self.value is None or self.value == "") and len(self.choices) > 0:
            self.value = self.choices[0]
        elif self.value not in self.choices and len(self.choices) > 0:
            self.value = self.choices[0]

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
