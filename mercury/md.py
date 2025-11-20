# markdown.py

import ipywidgets as widgets
import traitlets
from IPython.display import display

from .manager import WidgetsManager, MERCURY_MIMETYPE

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
            return md_lib.markdown(text)
        # Fallback: keep it visible, but not nicely formatted
        return f"<pre>{text}</pre>"

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
    code_uid = WidgetsManager.get_code_uid("Markdown", key=key)
    cached = WidgetsManager.get_widget(code_uid)

    if cached is not None:
        widget: MarkdownWidget = cached
        widget.text = text
        widget.position = position
        return widget

    widget = MarkdownWidget(text=text, position=position)
    WidgetsManager.add_widget(code_uid, widget)
    return widget
