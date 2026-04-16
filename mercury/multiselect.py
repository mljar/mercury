# Copyright MLJAR Sp. z o.o.
# Licensed under the Apache License, Version 2.0 (Apache-2.0)

import warnings
from typing import List, Literal

import anywidget
import traitlets
from IPython.display import display

from .manager import MERCURY_MIMETYPE, WidgetsManager
from .theme import THEME
from .url_params import resolve_multiselect_value

Position = Literal["sidebar", "inline", "bottom"]


def MultiSelect(
    label: str = "Select",
    value: List[str] | None = None,
    choices: List[str] = [],
    url_key: str = "",
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
    url_key : str, optional
        URL query parameter name used to override the initial value.
        Repeated params are supported. Empty or invalid values fall back to ``value``.
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
    if len(set(choices)) != len(choices):
        raise Exception("MultiSelect: `choices` must not contain duplicate values.")

    value = resolve_multiselect_value(value=value, url_key=url_key, choices=choices)

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

    args = [value, label, choices, url_key, placeholder, position]
    kwargs = {
        "value": value,
        "label": label, 
        "choices": choices,
        "url_key": url_key,
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
      const normalize = value => String(value ?? "").toLowerCase().trim();
      const getSelected = () =>
        Array.isArray(model.get("value")) ? [...model.get("value")] : [];
      const getChoices = () =>
        Array.isArray(model.get("choices")) ? [...model.get("choices")] : [];
      const isDisabled = () => !!model.get("disabled");
      const isHidden = () => !!model.get("hidden");

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

      const selectedWrap = document.createElement("div");
      selectedWrap.classList.add("mljar-ms-selected");

      const input = document.createElement("input");
      input.type = "text";
      input.classList.add("mljar-ms-input");
      input.autocomplete = "off";
      input.spellcheck = false;
      input.placeholder = model.get("placeholder") || "";

      const clearBtn = document.createElement("button");
      clearBtn.type = "button";
      clearBtn.classList.add("mljar-ms-clear");
      clearBtn.setAttribute("aria-label", "Clear selected values");
      clearBtn.setAttribute("title", "Clear selected values");
      clearBtn.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
          <path d="M18 6l-12 12"></path>
          <path d="M6 6l12 12"></path>
        </svg>
      `;

      const caret = document.createElement("div");
      caret.classList.add("mljar-ms-caret");

      control.appendChild(selectedWrap);
      control.appendChild(clearBtn);
      control.appendChild(caret);

      const dropdown = document.createElement("div");
      dropdown.classList.add("mljar-ms-dropdown");
      const list = document.createElement("div");
      list.classList.add("mljar-ms-list");
      const emptyState = document.createElement("div");
      emptyState.classList.add("mljar-ms-empty");
      emptyState.textContent = "No matches";
      dropdown.appendChild(list);
      dropdown.appendChild(emptyState);

      container.appendChild(control);
      container.appendChild(dropdown);
      el.appendChild(container);

      let isOpen = false;
      let isEditing = false;
      let filteredChoices = [];
      let blurTimeout = null;

      const setOpen = next => {
        if (isDisabled()) {
          isOpen = false;
        } else {
          isOpen = !!next;
        }
        container.classList.toggle("is-open", isOpen);
        dropdown.style.display = isOpen ? "block" : "none";
      };

      const syncEditingState = () => {
        const hasSelection = getSelected().length > 0;
        container.classList.toggle("is-editing", isEditing);
        container.classList.toggle("has-selection", hasSelection);
        control.classList.toggle("has-selection", hasSelection);
        clearBtn.classList.toggle("is-visible", hasSelection && !isDisabled());
      };

      const updateDisabledState = () => {
        const disabled = isDisabled();
        input.disabled = disabled;
        clearBtn.disabled = disabled;
        control.classList.toggle("is-disabled", disabled);
      };

      const updateHiddenState = () => {
        container.style.display = isHidden() ? "none" : "";
      };

      const renderSummary = () => {
        const selected = getSelected();
        selectedWrap.innerHTML = "";
        if (selected.length === 0) {
          selectedWrap.classList.add("is-empty");
          input.placeholder = model.get("placeholder") || "";
          selectedWrap.appendChild(input);
          return;
        }
        selectedWrap.classList.remove("is-empty");
        input.placeholder = "";
        selected.forEach(choice => {
          const chip = document.createElement("div");
          chip.classList.add("mljar-ms-chip");

          const label = document.createElement("span");
          label.classList.add("mljar-ms-chip-label");
          label.textContent = choice;

          const removeBtn = document.createElement("button");
          removeBtn.type = "button";
          removeBtn.classList.add("mljar-ms-chip-remove");
          removeBtn.innerHTML = "&times;";
          removeBtn.disabled = isDisabled();
          removeBtn.addEventListener("mousedown", event => {
            event.preventDefault();
            event.stopPropagation();
            const nextSelected = getSelected().filter(value => value !== choice);
            model.set("value", nextSelected);
            model.save_changes();
            input.focus();
          });

          chip.appendChild(label);
          chip.appendChild(removeBtn);
          selectedWrap.appendChild(chip);
        });
        selectedWrap.appendChild(input);
        syncEditingState();
      };

      const filterChoices = query => {
        const normalizedQuery = normalize(query);
        const allChoices = getChoices();
        const selected = new Set(getSelected());
        const availableChoices = allChoices.filter(choice => !selected.has(choice));
        if (!normalizedQuery) {
          return availableChoices;
        }
        return availableChoices.filter(choice =>
          normalize(choice).includes(normalizedQuery)
        );
      };

      const commitSelection = choice => {
        const selected = new Set(getSelected());
        if (selected.has(choice)) {
          selected.delete(choice);
        } else {
          selected.add(choice);
        }
        model.set("value", [...selected]);
        model.save_changes();
      };

      const renderList = () => {
        const selected = new Set(getSelected());
        list.innerHTML = "";
        filteredChoices.forEach(choice => {
          const option = document.createElement("button");
          option.type = "button";
          option.classList.add("mljar-ms-option");
          if (selected.has(choice)) {
            option.classList.add("is-selected");
          }

          const marker = document.createElement("span");
          marker.classList.add("mljar-ms-option-marker");
          marker.textContent = selected.has(choice) ? "✓" : "";

          const label = document.createElement("span");
          label.classList.add("mljar-ms-option-label");
          label.textContent = choice;

          option.appendChild(marker);
          option.appendChild(label);

          option.addEventListener("mousedown", event => {
            event.preventDefault();
            event.stopPropagation();
            commitSelection(choice);
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
        if (blurTimeout !== null) {
          window.clearTimeout(blurTimeout);
          blurTimeout = null;
        }
        isEditing = true;
        input.value = "";
        syncEditingState();
        refreshList();
        setOpen(true);
      };

      control.addEventListener("click", event => {
        event.stopPropagation();
        if (isDisabled()) {
          return;
        }
        if (event.target === input || clearBtn.contains(event.target)) {
          return;
        }
        openWithCurrentQuery();
        input.focus();
      });

      clearBtn.addEventListener("mousedown", event => {
        event.preventDefault();
        event.stopPropagation();
        if (isDisabled()) {
          return;
        }
        if (blurTimeout !== null) {
          window.clearTimeout(blurTimeout);
          blurTimeout = null;
        }
        isEditing = false;
        model.set("value", []);
        model.save_changes();
        input.value = "";
        setOpen(false);
        syncEditingState();
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
        if (blurTimeout !== null) {
          window.clearTimeout(blurTimeout);
        }
        blurTimeout = window.setTimeout(() => {
          isEditing = false;
          input.value = "";
          syncEditingState();
          blurTimeout = null;
        }, 120);
      });

      const handleDocumentClick = event => {
        if (!container.contains(event.target)) {
          if (blurTimeout !== null) {
            window.clearTimeout(blurTimeout);
            blurTimeout = null;
          }
          isEditing = false;
          setOpen(false);
          input.value = "";
          syncEditingState();
        }
      };

      document.addEventListener("click", handleDocumentClick);

      model.on("change:value", () => {
        renderSummary();
        refreshList();
      });
      model.on("change:choices", () => {
        renderSummary();
        refreshList();
      });
      model.on("change:disabled", () => {
        updateDisabledState();
        if (isDisabled()) {
          isEditing = false;
          setOpen(false);
          syncEditingState();
        }
      });
      model.on("change:hidden", () => {
        updateHiddenState();
      });

      updateDisabledState();
      updateHiddenState();
      renderSummary();
      refreshList();
      setOpen(false);
      syncEditingState();

      return () => {
        if (blurTimeout !== null) {
          window.clearTimeout(blurTimeout);
        }
        document.removeEventListener("click", handleDocumentClick);
      };
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
      position: relative;
      display: flex;
      align-items: center;
      width: 100%;
      min-height: 40px;
      padding: 4px 60px 4px 8px;
      border: 1px solid {THEME.get('border_color', '#ccc')};
      border-radius: {THEME.get('border_radius', '6px')};
      background: #fff;
      box-sizing: border-box;
      transition: border-color 0.15s ease, box-shadow 0.15s ease;
      cursor: default;
    }}

    .mljar-ms-control:focus-within {{
      border-color: {THEME.get('accent_color', '#4c7cf0')};
      box-shadow: 0 0 0 3px rgba(76, 124, 240, 0.16);
    }}

    .mljar-ms-selected {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      align-items: center;
      flex: 1 1 auto;
      min-width: 0;
      min-height: 30px;
      width: 100%;
    }}

    .mljar-ms-control.has-selection .mljar-ms-selected {{
      max-width: 100%;
    }}

    .mljar-ms-container.has-selection:not(.is-editing) .mljar-ms-selected {{
      flex: 1 1 auto;
    }}

    .mljar-ms-chip {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      max-width: 100%;
      min-height: 28px;
      padding: 3px 8px;
      border-radius: 999px;
      background: #eef3ff;
      color: #1f4fd1;
      box-sizing: border-box;
    }}

    .mljar-ms-chip-label {{
      min-width: 0;
      word-break: break-word;
    }}

    .mljar-ms-chip-remove {{
      border: 0;
      background: transparent;
      color: inherit;
      cursor: pointer;
      font: inherit;
      font-size: 14px;
      line-height: 1;
      padding: 0;
      opacity: 0.75;
    }}

    .mljar-ms-chip-remove:hover:enabled {{
      opacity: 1;
    }}

    .mljar-ms-chip-remove:disabled {{
      cursor: not-allowed;
      opacity: 0.45;
    }}

    .mljar-ms-input {{
      flex: 1 1 48px;
      min-width: 32px;
      max-width: none;
      padding: 3px 0;
      border: 0;
      background: #fff;
      box-sizing: border-box;
      appearance: none !important;
      background-color: #ffffff !important;
      color: {THEME.get('text_color', '#222')} !important;
      line-height: 1.4;
      cursor: default;
      opacity: 1;
      transform: translateY(0);
      transition:
        flex-basis 0.18s ease,
        width 0.18s ease,
        max-width 0.18s ease,
        padding 0.18s ease,
        opacity 0.18s ease,
        transform 0.18s ease;
    }}

    .mljar-ms-control.has-selection .mljar-ms-input {{
      flex: 1 1 48px;
      width: auto;
      min-width: 32px;
      max-width: 100%;
      padding-right: 0;
    }}

    .mljar-ms-container.has-selection:not(.is-editing) .mljar-ms-input {{
      flex: 0 0 0;
      min-width: 0;
      max-width: 0;
      width: 0;
      padding: 0;
      opacity: 0;
      transform: translateY(-4px);
      pointer-events: none;
      overflow: hidden;
    }}

    .mljar-ms-input:focus {{
      outline: none;
      cursor: text;
    }}

    .mljar-ms-clear {{
      position: absolute;
      right: 30px;
      top: 50%;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 18px;
      height: 18px;
      margin: 0;
      padding: 0;
      border: 0;
      background: transparent;
      color: {THEME.get('text_color', '#222')};
      cursor: pointer;
      opacity: 0;
      transform: translateY(-50%) scale(0.9);
      pointer-events: none;
      transition: opacity 0.18s ease, transform 0.18s ease;
    }}

    .mljar-ms-clear svg {{
      display: block;
    }}

    .mljar-ms-clear.is-visible {{
      opacity: 0.5;
      transform: translateY(-50%) scale(1);
      pointer-events: auto;
    }}

    .mljar-ms-clear:hover:enabled {{
      opacity: 1;
    }}

    .mljar-ms-clear:focus-visible {{
      outline: none;
      opacity: 1;
    }}

    .mljar-ms-clear:disabled {{
      cursor: not-allowed;
      opacity: 0;
      pointer-events: none;
    }}

    .mljar-ms-caret {{
      position: absolute;
      right: 12px;
      top: 50%;
      width: 8px;
      height: 8px;
      border-right: 1.5px solid {THEME.get('text_color', '#222')};
      border-bottom: 1.5px solid {THEME.get('text_color', '#222')};
      transform: translateY(-65%) rotate(45deg);
      pointer-events: none;
      opacity: 0.5;
      transition: transform 0.18s ease, opacity 0.18s ease;
    }}

    .mljar-ms-container.is-open .mljar-ms-caret {{
      opacity: 1;
      transform: translateY(-35%) rotate(225deg);
    }}

    .mljar-ms-dropdown {{
      display: none;
      margin-top: 6px;
      border: 1px solid {THEME.get('border_color', '#ccc')};
      border-radius: {THEME.get('border_radius', '6px')};
      background: #fff;
      box-shadow: 0 8px 24px rgba(15, 23, 42, 0.12);
      overflow: hidden;
    }}

    .mljar-ms-list {{
      max-height: 260px;
      overflow-y: auto;
    }}

    .mljar-ms-option {{
      display: flex;
      align-items: center;
      gap: 8px;
      width: 100%;
      padding: 9px 10px;
      border: 0;
      background: transparent;
      color: {THEME.get('text_color', '#222')};
      text-align: left;
      cursor: pointer;
      font: inherit;
    }}

    .mljar-ms-option:hover {{
      background: #f5f7fb;
    }}

    .mljar-ms-option.is-selected {{
      background: #eef3ff;
      color: #1f4fd1;
      font-weight: 600;
    }}

    .mljar-ms-option-marker {{
      width: 16px;
      flex: 0 0 16px;
      text-align: center;
      color: #1f4fd1;
      font-weight: 700;
    }}

    .mljar-ms-option-label {{
      flex: 1 1 auto;
      min-width: 0;
    }}

    .mljar-ms-empty {{
      display: none;
      padding: 10px;
      color: #777;
      font-size: 0.95em;
    }}

    .mljar-ms-input:disabled {{
      background: transparent;
      color: #888;
      cursor: not-allowed;
    }}

    .mljar-ms-control.is-disabled {{
      background: #f5f5f5;
      cursor: not-allowed;
    }}

    .mljar-ms-control.is-disabled .mljar-ms-clear {{
      opacity: 0;
      pointer-events: none;
    }}

    .mljar-ms-control.is-disabled .mljar-ms-caret {{
      opacity: 0.45;
    }}
    """

    value = traitlets.List(traitlets.Unicode(), default_value=[]).tag(sync=True)
    choices = traitlets.List(traitlets.Unicode(), default_value=[]).tag(sync=True)
    label = traitlets.Unicode(default_value="Select").tag(sync=True)
    url_key = traitlets.Unicode(default_value="").tag(sync=True)
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
