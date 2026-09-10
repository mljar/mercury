# markdown.py

from html import escape
from html.parser import HTMLParser

import ipywidgets as widgets
import traitlets
from IPython.display import display

from .manager import WidgetsManager, MERCURY_MIMETYPE
from .render_context import apply_widget_render_metadata, with_widget_render_metadata
from .theme import THEME
from ._markdown import render_markdown


class _InlineStyleParser(HTMLParser):
    """Style actual elements, never tag-like text inside attribute values."""

    def __init__(self, tag, style):
        super().__init__(convert_charrefs=False)
        self.tag = tag
        self.style = style
        self.parts = []

    def handle_starttag(self, tag, attrs):
        self._start(tag, attrs, ">")

    def handle_startendtag(self, tag, attrs):
        self._start(tag, attrs, " />")

    def _start(self, tag, attrs, closing):
        if tag != self.tag:
            self.parts.append(self.get_starttag_text())
            return
        attrs = dict(attrs)
        attrs["style"] = (
            f"{attrs['style']}; {self.style}" if attrs.get("style") else self.style
        )
        serialized = "".join(
            f' {name}="{escape(value, quote=True)}"' if value is not None else f" {name}"
            for name, value in attrs.items()
        )
        self.parts.append(f"<{tag}{serialized}{closing}")

    def handle_endtag(self, tag):
        self.parts.append(f"</{tag}>")

    def handle_data(self, data):
        self.parts.append(data)

    def handle_entityref(self, name):
        self.parts.append(f"&{name};")

    def handle_charref(self, name):
        self.parts.append(f"&#{name};")

    def handle_comment(self, data):
        self.parts.append(f"<!--{data}-->")

    def handle_decl(self, decl):
        self.parts.append(f"<!{decl}>")


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

    def __init__(
        self, text: str = "hello", position: str = "inline", *,
        unsafe_allow_html: bool = False, **kwargs
    ):
        self.unsafe_allow_html = unsafe_allow_html
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
        """Sanitize rendered content before adding trusted theme styles."""
        body = render_markdown(text, unsafe_allow_html=self.unsafe_allow_html)
        return self._apply_inline_theme(body)

    def _add_inline_style(self, html: str, tag: str, style: str) -> str:
        parser = _InlineStyleParser(tag, style)
        parser.feed(html)
        parser.close()
        return "".join(parser.parts)

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
    *,
    unsafe_allow_html: bool = False,
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
    unsafe_allow_html : bool
        Bypass HTML sanitization for trusted content only. Defaults to False.
        Never enable for user input, uploaded files, or API/LLM responses.

    Returns
    -------
    MarkdownWidget
        The widget instance.
    """
    args = [text, position]
    kwargs = {"text": text, "position": position, "unsafe_allow_html": unsafe_allow_html}

    code_uid = WidgetsManager.get_code_uid("Markdown", key=key, args=args, kwargs=kwargs)
    cached = WidgetsManager.get_widget(code_uid)

    if cached is not None:
        widget: MarkdownWidget = cached
        widget.unsafe_allow_html = unsafe_allow_html
        widget.text = text
        widget.position = position
        apply_widget_render_metadata(widget)
        display(widget)
        return widget

    widget = MarkdownWidget(**with_widget_render_metadata(kwargs))
    WidgetsManager.add_widget(code_uid, widget)
    display(widget)
    return widget
