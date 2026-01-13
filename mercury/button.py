# Copyright MLJAR Sp. z o.o.
# Licensed under the Apache License, Version 2.0 (Apache-2.0)

from typing import Literal

import anywidget
import traitlets
from IPython.display import display

from .manager import MERCURY_MIMETYPE, WidgetsManager
from .theme import THEME

Position = Literal["sidebar", "inline", "bottom"]
Variant = Literal["primary", "secondary", "outline", "danger"]
Size = Literal["sm", "md", "lg"]


def Button(
    label: str = "Run",
    variant: Variant = "primary",
    size: Size = "md",
    position: Position = "sidebar",
    disabled: bool = False,
    hidden: bool = False,
    key: str = "",
):
    """
    Create and display a Button widget.

    This function instantiates a `ButtonWidget` with the given label and style.
    If a widget with the same configuration (identified by a unique code UID
    generated from widget type, arguments, and keyword arguments) already exists
    in the `WidgetsManager`, the existing instance is returned and displayed.

    Parameters
    ----------
    label : str
        Text displayed on the button.
        The default is `"Run"`.
    variant : {"primary", "secondary", "outline", "danger"}, optional
        Visual style variant of the button.
        The default is `"primary"`.
    size : {"sm", "md", "lg"}, optional
        Size of the button.
        The default is `"md"`.
    position : {"sidebar", "inline", "bottom"}, optional
        Controls where the widget is displayed:

        - `"sidebar"` — place the widget in the left sidebar panel (default).
        - `"inline"` — render the widget directly in the notebook flow.
        - `"bottom"` — render the widget after all notebook cells.
    disabled : bool, optional
        If `True`, the widget is rendered but cannot be interacted with.
    hidden : bool, optional
        If `True`, the widget exists but is not visible in the UI.
    key : str, optional
        Unique identifier used to differentiate widgets with the same parameters.

    Returns
    -------
    ButtonWidget
        The created or retrieved Button widget instance.

    Examples
    --------
    Basic usage:

    >>> from mercury import Button
    >>> btn = Button(label="Run", variant="primary")

    After the user clicks the button:

    >>> btn.value
    True
    >>> btn.n_clicks
    1
    """

    args = [label, variant, size, position]
    kwargs = {
        "label": label,
        "variant": variant,
        "size": size,
        "position": position
    }

    code_uid = WidgetsManager.get_code_uid("Button", key=key, args=args, kwargs=kwargs)
    cached = WidgetsManager.get_widget(code_uid)
    if cached:
        display(cached)
        return cached

    instance = ButtonWidget(**kwargs)
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

      function syncFromModel() {
        // label
        btn.textContent = model.get("label") || "Run";

        // variant
        const v = model.get("variant") || "primary";
        ["is-primary","is-secondary","is-outline","is-danger"].forEach(c => btn.classList.remove(c));
        btn.classList.add(`is-${v}`);

        // size
        const s = model.get("size") || "md";
        ["is-sm","is-md","is-lg"].forEach(c => btn.classList.remove(c));
        btn.classList.add(`is-${s}`);

        // disabled
        btn.disabled = !!model.get("disabled");

        // hidden (exists but not visible)
        container.style.display = model.get("hidden") ? "none" : "inline-flex";
      }

      btn.addEventListener("click", () => {
        if (model.get("disabled")) return;
        const current = model.get("n_clicks") || 0;
        model.set("n_clicks", current + 1);
        model.set("last_clicked_at", new Date().toISOString());
        model.set("value", true);
        model.save_changes();
        // model.send({ type: "clicked", n_clicks: current + 1 });
      });

      // Reactivity
      model.on("change:label", syncFromModel);
      model.on("change:variant", syncFromModel);
      model.on("change:size", syncFromModel);
      model.on("change:disabled", syncFromModel);
      model.on("change:hidden", syncFromModel);

      container.appendChild(btn);
      el.appendChild(container);

      syncFromModel();
    }
    export default { render };
    """

    _css = f"""
    .mljar-button-container {{
        display: inline-flex;
        width: auto;
        font-family: {THEME.get('font_family', 'Arial, sans-serif')};
        margin-bottom: 8px;
        padding-left: 4px;
        padding-right: 4px;
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

    label = traitlets.Unicode(default_value="Run").tag(sync=True)
    variant = traitlets.Enum(["primary", "secondary", "outline", "danger"], default_value="primary").tag(sync=True)
    size = traitlets.Enum(["sm", "md", "lg"], default_value="md").tag(sync=True)

    disabled = traitlets.Bool(default_value=False).tag(sync=True)
    hidden = traitlets.Bool(default_value=False).tag(sync=True)

    value = traitlets.Bool(default_value=False).tag(sync=True)
    n_clicks = traitlets.Int(default_value=0).tag(sync=True)
    last_clicked_at = traitlets.Unicode(default_value="").tag(sync=True)

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
