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

    args = [value, label, choices, position]
    kwargs = {
        "value": value,
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
      const normalize = value => String(value ?? "").toLowerCase().trim();
      const getChoices = () =>
        Array.isArray(model.get("choices")) ? [...model.get("choices")] : [];
      const isDisabled = () => !!model.get("disabled");
      const isHidden = () => !!model.get("hidden");

      const container = document.createElement("div");
      container.classList.add("mljar-select-container");

      if (model.get("label")) {
        const topLabel = document.createElement("div");
        topLabel.classList.add("mljar-select-label");
        topLabel.innerHTML = model.get("label");
        container.appendChild(topLabel);
      }

      const control = document.createElement("div");
      control.classList.add("mljar-select-control");

      const input = document.createElement("input");
      input.type = "text";
      input.classList.add("mljar-select-widget-input");
      input.autocomplete = "off";
      input.spellcheck = false;

      const caret = document.createElement("div");
      caret.classList.add("mljar-select-caret");
      caret.innerHTML = "&#9662;";

      control.appendChild(input);
      control.appendChild(caret);

      const dropdown = document.createElement("div");
      dropdown.classList.add("mljar-select-dropdown");

      const list = document.createElement("div");
      list.classList.add("mljar-select-list");

      const emptyState = document.createElement("div");
      emptyState.classList.add("mljar-select-empty");
      emptyState.textContent = "No matches";

      dropdown.appendChild(list);
      dropdown.appendChild(emptyState);

      container.appendChild(control);
      container.appendChild(dropdown);
      el.appendChild(container);

      let isOpen = false;
      let filteredChoices = [];
      let lastCommittedValue = "";
      let isEditing = false;

      const setOpen = next => {
        if (isDisabled()) {
          isOpen = false;
        } else {
          isOpen = !!next;
        }
        container.classList.toggle("is-open", isOpen);
        dropdown.style.display = isOpen ? "block" : "none";
      };

      const updateDisabledState = () => {
        const disabled = isDisabled();
        input.disabled = disabled;
        control.classList.toggle("is-disabled", disabled);
      };

      const updateHiddenState = () => {
        container.style.display = isHidden() ? "none" : "";
      };

      const syncInputWithValue = () => {
        const value = model.get("value") || "";
        lastCommittedValue = value;
        if (!isEditing) {
          input.value = value;
        }
      };

      const filterChoices = query => {
        const normalizedQuery = normalize(query);
        const allChoices = getChoices();
        if (!normalizedQuery) {
          return allChoices;
        }
        return allChoices.filter(choice =>
          normalize(choice).includes(normalizedQuery)
        );
      };

      const renderList = () => {
        list.innerHTML = "";
        filteredChoices.forEach(choice => {
          const option = document.createElement("button");
          option.type = "button";
          option.classList.add("mljar-select-option");
          if (choice === model.get("value")) {
            option.classList.add("is-selected");
          }
          option.textContent = choice;
          option.addEventListener("mousedown", event => {
            event.preventDefault();
            event.stopPropagation();
            model.set("value", choice);
            model.save_changes();
            isEditing = false;
            syncInputWithValue();
            renderList();
            setOpen(false);
          });
          list.appendChild(option);
        });

        const hasMatches = filteredChoices.length > 0;
        list.style.display = hasMatches ? "block" : "none";
        emptyState.style.display = hasMatches ? "none" : "block";
      };

      const refreshList = () => {
        filteredChoices = filterChoices(input.value);
        renderList();
      };

      const openWithCurrentQuery = () => {
        isEditing = true;
        input.value = "";
        refreshList();
        setOpen(true);
      };

      control.addEventListener("click", event => {
        event.stopPropagation();
        if (isDisabled()) {
          return;
        }
        openWithCurrentQuery();
        input.focus();
      });

      input.addEventListener("input", () => {
        if (isDisabled()) {
          return;
        }
        refreshList();
        setOpen(true);
      });

      input.addEventListener("focus", () => {
        if (isDisabled()) {
          return;
        }
        openWithCurrentQuery();
      });

      input.addEventListener("blur", () => {
        isEditing = false;
        input.value = lastCommittedValue;
      });

      const handleDocumentClick = event => {
        if (!container.contains(event.target)) {
          isEditing = false;
          setOpen(false);
          input.value = lastCommittedValue;
        }
      };

      document.addEventListener("click", handleDocumentClick);

      model.on("change:value", () => {
        syncInputWithValue();
        refreshList();
      });

      model.on("change:choices", () => {
        const choices = getChoices();
        if (!choices.includes(model.get("value")) && choices.length > 0) {
          model.set("value", choices[0]);
          model.save_changes();
          return;
        }
        syncInputWithValue();
        refreshList();
      });

      model.on("change:disabled", () => {
        updateDisabledState();
        if (isDisabled()) {
          isEditing = false;
          setOpen(false);
        }
      });

      model.on("change:hidden", () => {
        updateHiddenState();
      });

      updateDisabledState();
      updateHiddenState();
      syncInputWithValue();
      refreshList();
      setOpen(false);

      return () => {
        document.removeEventListener("click", handleDocumentClick);
      };
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

    .mljar-select-control {{
      position: relative;
      display: flex;
      align-items: center;
    }}

    .mljar-select-widget-input {{
      width: 100%;
      padding: 8px 36px 8px 10px;
      border: 1px solid {THEME.get('border_color', '#ccc')};
      border-radius: {THEME.get('border_radius', '6px')};
      background: #fff;
      box-sizing: border-box;
      transition: border-color 0.15s ease, box-shadow 0.15s ease;

      appearance: none !important;
      background-color: #ffffff !important;
      color: {THEME.get('text_color', '#222')} !important;
    }}

    .mljar-select-widget-input:focus {{
      outline: none;
      border-color: {THEME.get('accent_color', '#4c7cf0')};
      box-shadow: 0 0 0 3px rgba(76, 124, 240, 0.16);
    }}

    .mljar-select-caret {{
      position: absolute;
      right: 12px;
      top: 50%;
      transform: translateY(-50%);
      color: {THEME.get('text_color', '#222')};
      pointer-events: none;
      font-size: 11px;
      opacity: 0.7;
    }}

    .mljar-select-container.is-open .mljar-select-caret {{
      opacity: 1;
    }}

    .mljar-select-dropdown {{
      display: none;
      margin-top: 6px;
      border: 1px solid {THEME.get('border_color', '#ccc')};
      border-radius: {THEME.get('border_radius', '6px')};
      background: #fff;
      box-shadow: 0 8px 24px rgba(15, 23, 42, 0.12);
      overflow: hidden;
    }}

    .mljar-select-list {{
      max-height: 260px;
      overflow-y: auto;
    }}

    .mljar-select-option {{
      display: block;
      width: 100%;
      padding: 9px 10px;
      border: 0;
      background: transparent;
      color: {THEME.get('text_color', '#222')};
      text-align: left;
      cursor: pointer;
      font: inherit;
    }}

    .mljar-select-option:hover {{
      background: #f5f7fb;
    }}

    .mljar-select-option.is-selected {{
      background: #eef3ff;
      color: #1f4fd1;
      font-weight: 600;
    }}

    .mljar-select-empty {{
      display: none;
      padding: 10px;
      color: #777;
      font-size: 0.95em;
    }}

    .mljar-select-widget-input:disabled {{
      background: #f5f5f5;
      color: #888;
      cursor: not-allowed;
    }}

    .mljar-select-control.is-disabled .mljar-select-caret {{
      opacity: 0.45;
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
