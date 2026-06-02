# markdown.py

from html import escape
import re

import ipywidgets as widgets
import traitlets
from IPython.display import display

from .manager import WidgetsManager, MERCURY_MIMETYPE
from .render_context import apply_widget_render_metadata, with_widget_render_metadata
from .theme import THEME

try:
    # Optional: nice markdown → HTML conversion
    import markdown as md_lib
except ImportError:
    md_lib = None


class MarkdownWidget(widgets.HTML):
    """
    Markdown widget rendered as an ipywidgets.HTML, with Mercury
    'position' support (inline / sidebar / bottom).

    Because this is a real ipywidget (DOMWidget):
      - it has a model_id
      - Jupyter emits application/vnd.jupyter.widget-view+json
      - Mercury can read MERCURY_MIMETYPE from output.data
    """

    position = traitlets.Enum(
        values=["sidebar", "inline", "bottom"],
        default_value="inline",
        help="Widget placement: sidebar, inline, or bottom",
    ).tag(sync=True)
    cell_id = traitlets.Unicode(allow_none=True).tag(sync=True)
    source_cell_id = traitlets.Unicode(default_value=None, allow_none=True).tag(sync=True)
    render_slot_id = traitlets.Unicode(default_value=None, allow_none=True).tag(sync=True)
    layout_path = traitlets.Unicode(default_value=None, allow_none=True).tag(sync=True)

    def __init__(self, text: str = "hello", position: str = "inline", **kwargs):
        # store raw markdown
        self._raw_text = text

        # convert to HTML
        html = self._to_html(text)

        super().__init__(value=html, **kwargs)

        if position not in ("inline", "sidebar", "bottom"):
            raise ValueError("position must be one of: 'inline', 'sidebar', 'bottom'")
        self.position = position

    # -------- markdown → HTML handling ----------------------------------------

    def _to_html(self, text: str) -> str:
        """Convert markdown to HTML if possible; otherwise use <pre>."""
        if md_lib is not None:
            body = md_lib.markdown(text)
        else:
            # Fallback: keep it visible, but not nicely formatted
            body = f"<pre>{escape(text)}</pre>"

        return self._apply_inline_theme(body)

    def _add_inline_style(self, html: str, tag: str, style: str) -> str:
        pattern = rf"<{tag}(\s[^>]*)?>"

        def repl(match):
            attrs = match.group(1) or ""
            if "style=" in attrs:
                return re.sub(
                    r'style=(["\'])(.*?)\1',
                    lambda m: f'style={m.group(1)}{m.group(2)}; {style}{m.group(1)}',
                    match.group(0),
                    count=1,
                )
            return f"<{tag}{attrs} style=\"{style}\">"

        return re.sub(pattern, repl, html)

    def _apply_inline_theme(self, body: str) -> str:
        radius_sm = THEME.get("border_radius_sm", "4px")
        radius = THEME.get("border_radius", "6px")
        heading_font = THEME.get("heading_font_family", THEME.get("font_family"))
        heading_weight = THEME.get("heading_font_weight", "800")

        for tag, size in (
            ("h1", "2.0em"),
            ("h2", "1.6em"),
            ("h3", "1.35em"),
            ("h4", "1.15em"),
            ("h5", "1em"),
            ("h6", "0.92em"),
        ):
            body = self._add_inline_style(
                body,
                tag,
                f"font-family: {heading_font}; font-weight: {heading_weight}; color: {THEME.get('text_color')}; line-height: 1.25; margin: 1.15em 0 0.45em; font-size: {size};",
            )

        body = self._add_inline_style(body, "p", "margin: 0 0 1em;")
        body = self._add_inline_style(body, "ul", "margin: 0 0 1em; padding-left: 1.4em;")
        body = self._add_inline_style(body, "ol", "margin: 0 0 1em; padding-left: 1.4em;")
        body = self._add_inline_style(
            body,
            "a",
            f"color: {THEME.get('primary_color')}; text-decoration: underline; text-underline-offset: 0.14em;",
        )
        body = self._add_inline_style(body, "strong", "font-weight: 700;")
        body = self._add_inline_style(
            body,
            "code",
            f"font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace; font-size: 0.92em; color: {THEME.get('text_color')}; background: {THEME.get('panel_bg_hover', THEME.get('panel_bg'))}; border: 1px solid {THEME.get('border_color')}; border-radius: {radius_sm}; padding: 0.12em 0.38em;",
        )
        body = self._add_inline_style(
            body,
            "pre",
            f"margin: 0 0 1em; background: {THEME.get('panel_bg')}; border: 1px solid {THEME.get('border_color')}; border-radius: {radius}; color: {THEME.get('text_color')}; overflow-x: auto; padding: 0.85em 1em;",
        )
        body = self._add_inline_style(
            body,
            "blockquote",
            f"margin: 0 0 1em; padding-left: 1em; border-left: 3px solid {THEME.get('accent_color', THEME.get('primary_color'))}; color: {THEME.get('muted_text_color')};",
        )
        body = self._add_inline_style(
            body,
            "hr",
            f"border: 0; border-top: 1px solid {THEME.get('border_color')}; margin: 1.25em 0;",
        )
        body = self._add_inline_style(
            body,
            "table",
            "width: 100%; border-collapse: collapse; margin: 0 0 1em;",
        )
        body = self._add_inline_style(
            body,
            "th",
            f"border: 1px solid {THEME.get('border_color')}; padding: 0.55em 0.7em; text-align: left; background: {THEME.get('panel_bg_hover', THEME.get('panel_bg'))}; font-weight: 700;",
        )
        body = self._add_inline_style(
            body,
            "td",
            f"border: 1px solid {THEME.get('border_color')}; padding: 0.55em 0.7em; text-align: left;",
        )
        body = self._add_inline_style(
            body,
            "img",
            "max-width: 100%; height: auto;",
        )

        return (
            f"<div style=\"font-family: {THEME.get('font_family')}; "
            f"font-size: {THEME.get('font_size')}; "
            f"font-weight: {THEME.get('font_weight', 'normal')}; "
            f"line-height: 1.65; color: {THEME.get('text_color')}; "
            f"word-break: break-word;\">{body}</div>"
        )

    @property
    def text(self) -> str:
        return self._raw_text

    @text.setter
    def text(self, value: str) -> None:
        self._raw_text = value
        self.value = self._to_html(value)

    # -------- Jupyter / Mercury integration -----------------------------------

    def _repr_mimebundle_(self, **kwargs):
        """
        Use the standard ipywidgets HTML mimebundle, but inject
        MERCURY_MIMETYPE with model_id + position, just like Slider.
        """
        data = super()._repr_mimebundle_(**kwargs)

        # ipywidgets usually returns (bundle_dict, metadata_dict)
        if isinstance(data, tuple) and len(data) > 1:
            bundle, metadata = data

            mercury_mime = {
                "widget": type(self).__qualname__,
                "model_id": self.model_id,
                "position": self.position,
            }

            # IMPORTANT: put it into the bundle (this becomes output.data)
            bundle[MERCURY_MIMETYPE] = mercury_mime
            return bundle, metadata

        # Rare fallback: if it ever returns a single dict
        if isinstance(data, dict):
            mercury_mime = {
                "widget": type(self).__qualname__,
                "model_id": self.model_id,
                "position": self.position,
            }
            data[MERCURY_MIMETYPE] = mercury_mime
            return data

        return data


def Markdown(
    text: str = "hello",
    position: str = "inline",
    key: str = "",
) -> MarkdownWidget:
    """
    Display Markdown text with Mercury 'position' support.

    Parameters
    ----------
    text : str
        Markdown content (in Markdown syntax).
    position : {"inline", "sidebar", "bottom"}
        Where the widget should appear in the Mercury layout.
        Default is "inline" (main panel).
    key : str
        Optional cache key for reuse (same idea as in Slider/Columns).

    Returns
    -------
    MarkdownWidget
        The widget instance.
    """
    args = [text, position]
    kwargs = {"text": text, "position": position}

    code_uid = WidgetsManager.get_code_uid("Markdown", key=key, args=args, kwargs=kwargs)
    cached = WidgetsManager.get_widget(code_uid)

    if cached is not None:
        widget: MarkdownWidget = cached
        widget.text = text
        widget.position = position
        apply_widget_render_metadata(widget)
        display(widget)
        return widget

    widget = MarkdownWidget(**with_widget_render_metadata(kwargs))
    WidgetsManager.add_widget(code_uid, widget)
    display(widget)
    return widget
