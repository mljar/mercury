import os
import base64
import mimetypes
import ipywidgets as widgets
from IPython.display import display
from html import escape

from .manager import WidgetsManager
from .theme import THEME


# ---------- Global CSS (injected once) ----------
def _ensure_global_image_styles():
    css = f"""
    <style>
      .mljar-image-card {{
        width: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 6px;
        border: 1px solid {THEME.get('border_color', '#ddd')};
        border-radius: {THEME.get('border_radius', '8px')};
        background: {THEME.get('panel_bg', '#fff')};
        padding: 8px;
        box-sizing: border-box;
        overflow: hidden;
      }}

      .mljar-image-wrap {{
        width: 100%;
        position: relative;
        overflow: hidden;
        border-radius: {THEME.get('border_radius', '8px')};
      }}

      .mljar-image-wrap img {{
        display: block;
        max-width: 100%;
        height: auto;
      }}

      .mljar-image-caption {{
        font-family: {THEME.get('font_family', 'Arial, sans-serif')};
        font-size: 0.9em;
        color: {THEME.get('muted_text_color', THEME.get('text_color', '#444'))};
        font-style: italic;
        text-align: center;
      }}

      .mljar-image-card :is(.jupyter-widgets, .widget-box, .widget-hbox, .widget-vbox) {{
        margin-left: 0 !important;
        margin-right: 0 !important;
        max-width: 100%;
        box-sizing: border-box;
      }}
    </style>
    """
    display(widgets.HTML(css))


def _path_to_data_uri(path: str) -> str:
    """Read local file and return a data: URI with guessed MIME type."""
    mime, _ = mimetypes.guess_type(path)
    if not mime:
        mime = "image/png"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def _img_src(url_or_path: str) -> str:
    """Return an <img> src from URL or local file path (as data URI)."""
    if isinstance(url_or_path, str) and url_or_path.lower().startswith(("http://", "https://")):
        return url_or_path
    if isinstance(url_or_path, str) and os.path.exists(url_or_path):
        return _path_to_data_uri(url_or_path)
    return url_or_path


# ---------- Public API ----------
def ImageCard(src: str, caption: str = "",
              width: str = "100%", height: str | None = None,
              rounded: bool = True, show_border: bool = True,
              key: str = "") -> widgets.VBox:
    """
    Display an image from URL or local file with a caption (centered, italic).

    Parameters
    ----------
    src : str
        URL (http/https) or local file path.
    caption : str
        Optional caption text shown below the image (centered, italic).
    width : str
        CSS width for the outer card (e.g. '100%', '400px').
    height : str | None
        Fixed CSS height for the image area (e.g. '240px'). If None, image auto adjusts.
    rounded : bool
        Apply theme border radius to the image area.
    show_border : bool
        Show or hide the border around the image card.
    key : str
        Stable cache key to reuse the same widget instance.

    """
    _ensure_global_image_styles()

    code_uid = WidgetsManager.get_code_uid("ImageCard", key=key or src or "image", 
                kwargs=dict(src=src, caption=caption, width=width, 
                height=height, rounded=rounded, show_border=show_border
                ))
    cached = WidgetsManager.get_widget(code_uid)
    if cached:
        card = cached
        display(card)
        return

    img_src = _img_src(src)
    style_parts = ["width:100%;", "height:auto;"]
    if height:
        style_parts = ["width:100%;", f"height:{height};", "object-fit:contain;"]

    img_html = f'<img src="{escape(img_src, quote=True)}" alt="image" style={"".join(style_parts)} />'

    # Optional rounded style
    wrap_style = f"border-radius:{THEME.get('border_radius','8px')};" if rounded else "border-radius:0;"
    img_wrap = widgets.HTML(value=f'<div class="mljar-image-wrap" style="{wrap_style}">{img_html}</div>')

    # Caption
    cap_html = widgets.HTML(value=f'<div class="mljar-image-caption">{escape(caption)}</div>' if caption else "")

    # Card layout
    border_style = f"1px solid {THEME.get('border_color', '#ddd')}" if show_border else "none"
    card_layout = widgets.Layout(
        width=width,
        border=border_style,
        border_radius=THEME.get('border_radius', '8px'),
        padding="8px"
    )

    card = widgets.VBox([img_wrap, cap_html] if caption else [img_wrap], layout=card_layout)
    card.add_class("mljar-image-card")

    display(card)
    WidgetsManager.add_widget(code_uid, card)

