# Copyright MLJAR Sp. z o.o.
# Licensed under the Apache License, Version 2.0 (Apache-2.0)
 
import anywidget
import traitlets
import ipywidgets as widgets
from IPython.display import display

from .manager import WidgetsManager, MERCURY_MIMETYPE
from .render_context import LayoutContextOutput, LayoutFrame
from .theme import THEME

def _ensure_global_expander_styles():
    css = f"""
    <style>
      .mljar-expander-box {{
        width: 100%;
        border: 1px solid {THEME.get('border_color', '#ddd')};
        border-radius: {THEME.get('border_radius', '8px')};
        background: {THEME.get('panel_bg', '#fff')};
        overflow: hidden;
      }}

      .mljar-expander-box.is-borderless {{
        border: 0;
        border-radius: 0;
        background: transparent;
      }}

      .mljar-expander-content {{
        width: 100%;
        position: relative;
        box-sizing: border-box;
        overflow: hidden;
        max-height: 0;
        opacity: 0;
        padding: 0 10px;
        transform: translateY(-4px);
        transition:
          max-height 300ms cubic-bezier(0.25, 1, 0.5, 1),
          opacity 300ms cubic-bezier(0.25, 1, 0.5, 1),
          transform 300ms cubic-bezier(0.25, 1, 0.5, 1),
          padding-top 300ms ease,
          padding-bottom 300ms ease;
        will-change: max-height, opacity, transform;
      }}

      .mljar-expander-content > * {{
        overflow: hidden;
        min-height: 0;
        box-sizing: border-box;
      }}

      /* Fading divider (no layout shift) */
      .mljar-expander-content::before {{
        content: "";
        position: absolute;
        left: 0; right: 0; top: 0;
        height: 1px;
        background: {THEME.get('border_color', '#ddd')};
        opacity: 0;
        transition: opacity 300ms ease;
        pointer-events: none;
      }}
      .mljar-expander-box.is-borderless .mljar-expander-content::before {{
        background: transparent;
      }}

      /* Opened state – natural "ease-out" movement */
      .mljar-expander-content.is-open {{
        max-height: 1000vh;       /* big enough for all content */
        opacity: 1;
        padding-top: 10px;
        padding-bottom: 10px;
        transform: translateY(0);
      }}
      .mljar-expander-content.is-open::before {{
        opacity: 1;
      }}

      @media (prefers-reduced-motion: reduce) {{
        .mljar-expander-content {{
          transition: none;
          transform: none;
        }}
      }}
    </style>
    """
    style_html = widgets.HTML(css)
    display(style_html)


def _set_class(widget, class_name: str, enabled: bool) -> None:
    if enabled:
        widget.add_class(class_name)
    else:
        widget.remove_class(class_name)


def _clear_output_widget(out) -> None:
    out.clear_output(wait=True)
    if hasattr(out, "outputs"):
        out.outputs = ()


def Expander(
    label="Details",
    expanded=False,
    show_border=True,
    header_background=True,
    key="",
    append=False,
):
    """
    Create and display an Expander.

    The function returns an `ipywidgets.Output` that you can write into:

    >>> out = mr.Expander("Details")
    >>> with out:
    ...     print("Hello")

    Notes
    -----
    - Uses caching via WidgetsManager (stable `key` recommended).
    - Styling is injected once globally (theme-aware).
    - By default, reused content is cleared on each call. Set
      `append=True` to preserve previous content and append new output.
    """
    _ensure_global_expander_styles()

    code_uid = WidgetsManager.get_code_uid(
        "Expander",
        key=key,
        kwargs=dict(
            label=label,
            show_border=show_border,
            header_background=header_background,
        ),
    )
    cached = WidgetsManager.get_widget(code_uid)
    if cached:
        # Don't display again — that would append another copy in output.
        # Just return the existing Output area so user can write to it.
        _box, out, _header, _content_box = cached
        _set_class(_box, "is-borderless", not show_border)
        _header.label = label
        _header.header_background = bool(header_background)
        if not append:
            _clear_output_widget(out)
        display(_box)
        return out

    header = _ExpanderHeaderWidget(
        label=label,
        expanded=expanded,
        header_background=bool(header_background),
    )

    out = LayoutContextOutput(
        layout_frame=LayoutFrame(
            layout_type="expander",
            owner_id=code_uid,
            slot_key="content",
        )
    )
    out.layout.width = "100%"

    content_box = widgets.Box([out], layout=widgets.Layout(width="100%"))
    content_box.add_class("mljar-expander-content")
    if expanded:
        content_box.add_class("is-open")

    def _on_expand_change(change):
        if change["new"]:
            content_box.add_class("is-open")
        else:
            content_box.remove_class("is-open")
    header.observe(_on_expand_change, names="expanded")

    box = widgets.VBox([header, content_box], layout=widgets.Layout(width="100%"))
    box.add_class("mljar-expander-box")
    _set_class(box, "is-borderless", not show_border)

    # Only display on first creation
    display(box)
    WidgetsManager.add_widget(code_uid, (box, out, header, content_box))
    return out


class _ExpanderHeaderWidget(anywidget.AnyWidget):
    label = traitlets.Unicode("Details").tag(sync=True)
    expanded = traitlets.Bool(False).tag(sync=True)
    header_background = traitlets.Bool(True).tag(sync=True)
    custom_css = traitlets.Unicode(default_value="").tag(sync=True)
    position = traitlets.Enum(
        values=["sidebar", "inline", "bottom"],
        default_value="sidebar",
        help="Widget placement: sidebar, inline, or bottom",
    ).tag(sync=True)

    _esm = """
    function render({ model, el }) {
      const header = document.createElement("button");
      header.type = "button";
      header.classList.add("mljar-expander-header");
      header.setAttribute("aria-expanded", String(model.get("expanded")));

      const icon = document.createElement("span");
      icon.classList.add("mljar-expander-icon");
      const text = document.createElement("span");
      text.classList.add("mljar-expander-label");
      text.textContent = model.get("label") || "Details";

      header.appendChild(icon);
      header.appendChild(text);
      el.appendChild(header);

      function syncUI() {
        const isOpen = !!model.get("expanded");
        const hasBackground = !!model.get("header_background");
        header.setAttribute("aria-expanded", String(isOpen));
        header.classList.toggle("is-open", isOpen);
        header.classList.toggle("is-transparent", !hasBackground);
      }
      syncUI();

      header.addEventListener("click", () => {
        const next = !model.get("expanded");
        model.set("expanded", next);
        model.save_changes();
      });

      model.on("change:expanded", syncUI);
      model.on("change:header_background", syncUI);
      model.on("change:label", () => {
        text.textContent = model.get("label") || "Details";
      });

      const css = model.get("custom_css");
      if (css && css.trim().length > 0) {
        const styleTag = document.createElement("style");
        styleTag.textContent = css;
        el.appendChild(styleTag);
      }
    }
    export default { render };
    """

    _css = f"""
    .mljar-expander-header {{
      width: 100%;
      display: flex;
      align-items: center;
      gap: 8px;
      background: {THEME.get('panel_bg_hover', '#f7f7f9')};
      border: 0;
      padding: 8px 10px;
      cursor: pointer;
      text-align: left;
      font-family: {THEME.get('font_family', 'Arial, sans-serif')};
      font-size: {THEME.get('font_size', '14px')};
      font-weight: {THEME.get('font_weight', '600')};
      color: {THEME.get('text_color', '#222')};
      transition: background 0.15s ease;
      position: relative;
    }}
    .mljar-expander-header:hover {{
      background: {THEME.get('hover_background_color', THEME.get('panel_bg_hover_2', '#efefef'))};
    }}
    .mljar-expander-header:active {{
      background: {THEME.get('selected_background_color', '#eef3ff')};
    }}
    .mljar-expander-header:focus-visible {{
      outline: none;
      box-shadow: inset 0 0 0 2px {THEME.get('focus_border_color', THEME.get('accent_color', '#4c7cf0'))};
    }}
    .mljar-expander-header.is-transparent {{
      background: transparent;
    }}
    .mljar-expander-header.is-transparent:hover {{
      background: transparent;
    }}
    .mljar-expander-icon {{
      display: inline-block;
      width: 0;
      height: 0;
      border-left: 6px solid transparent;
      border-right: 6px solid transparent;
      border-top: 8px solid {THEME.get('primary_color', '#007bff')};
      transform: rotate(0deg);
      transition: transform 0.15s ease;
    }}
    .mljar-expander-header.is-open .mljar-expander-icon {{
      transform: rotate(180deg);
    }}
    .mljar-expander-label {{
      flex: 1 1 auto;
    }}
    """

    def _repr_mimebundle_(self, **kwargs):
        data = super()._repr_mimebundle_()
        if len(data) > 1:
            import json
            mercury_mime = {
                "widget": type(self).__qualname__,
                "model_id": self.model_id,
                "position": self.position,
            }
            data[0][MERCURY_MIMETYPE] = mercury_mime
        return data
