import ipywidgets as widgets
from IPython.display import HTML, display
import traitlets

from .manager import WidgetsManager, MERCURY_MIMETYPE
from .theme import THEME


def display_style():
    """Inject custom CSS styles for MLJAR widgets based on the active theme."""
    border_radius = THEME.get("border_radius", "4px")

    css = f"""
    <style>
    .mljar-column {{
        border-radius: {border_radius} !important;
    }}
    </style>
    """

    display(HTML(css))


class ColumnsBox(widgets.HBox):
    """
    Custom HBox that carries 'position' info for Mercury layout
    (sidebar / inline / bottom), similar to SliderWidget.
    """
    position = traitlets.Enum(
        values=["sidebar", "inline", "bottom"],
        default_value="inline",
        help="Widget placement: sidebar, inline, or bottom"
    ).tag(sync=True)

    def _repr_mimebundle_(self, **kwargs):
        data = super()._repr_mimebundle_(**kwargs)
        if len(data) > 1:
            mercury_mime = {
                "widget": type(self).__qualname__,
                "model_id": self.model_id,
                "position": self.position,
            }
            data[MERCURY_MIMETYPE] = mercury_mime
        return data

class ColumnOutput(widgets.Output):
    """Output widget with a convenient .clear() method."""
    def clear(self, wait=True):
        """Clear output (alias for clear_output)."""
        self.clear_output(wait=wait)

def Columns(
    n=2,
    min_width="100px",
    gap="16px",
    border=None,
    position="inline",
    key="",
):
    """
    Create a responsive row of Output widgets.

    Parameters
    ----------
    n : int
        Number of columns.
    min_width : str or None
        Minimum width for each column (e.g. '240px').
    gap : str
        Gap between columns (e.g. '16px').
    border : str or None
        CSS border style (e.g. '1px solid lightgray').
        Set to None or '' to disable borders.
    position : {"sidebar", "inline", "bottom"}
        Widget placement in the panel (Mercury layout).
        Default is "inline" (main panel).
    key : str
        Cache key for reuse.
    """
    kwargs = {
        "n": n,
        "min_width": min_width,
        "gap": gap,
        "border": border,
        "position": position,
    }
    code_uid = WidgetsManager.get_code_uid("Columns", key=key, args=[], kwargs=kwargs)
    cached = WidgetsManager.get_widget(code_uid)
    if cached:
        box, outs = cached
        # if you want, you can allow changing position on reuse:
        # box.position = position
        display_style()
        display(box)
        return outs

    outs = [ColumnOutput() for _ in range(n)]
    box = ColumnsBox(
        children=outs,
        layout=widgets.Layout(
            width="100%",
            display="flex",
            flex_flow="row wrap",
            gap=gap,
            align_items="stretch",
        ),
        position=position,
    )

    for out in outs:
        # size / layout
        out.layout.min_width = min_width
        out.layout.flex = "1 1 0px"

        out.add_class("mljar-column")

        show_border = THEME.get("border_visible", False)
        # if border is set in constructor please respect its value
        # over defaults from theme config.toml
        if border is not None:
            show_border = border
        if show_border:
            border_color = THEME.get("border_color", "lightgray")
            out.layout.border = f"1px solid {border_color}"
            out.layout.padding = "4px"
            out.layout.box_sizing = "border-box"

    display_style()
    display(box)
    WidgetsManager.add_widget(code_uid, (box, tuple(outs)))
    return tuple(outs)
