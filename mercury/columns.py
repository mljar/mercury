# Copyright MLJAR Sp. z o.o.
# Licensed under the Apache License, Version 2.0 (Apache-2.0)

from __future__ import annotations

from typing import Literal, Tuple

import ipywidgets as widgets
from IPython.display import HTML, display
import traitlets

from .manager import MERCURY_MIMETYPE, WidgetsManager
from .theme import THEME

Position = Literal["sidebar", "inline", "bottom"]


def _display_style():
    """Inject CSS for MLJAR Columns (theme-aware)."""
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
    Custom HBox that carries `position` info for Mercury layout
    (sidebar / inline / bottom), similar to other widgets.
    """

    position = traitlets.Enum(
        values=["sidebar", "inline", "bottom"],
        default_value="inline",
        help="Widget placement: sidebar, inline, or bottom",
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
    """Output widget with a convenient .clear() alias."""
    def clear(self, wait: bool = True):
        self.clear_output(wait=wait)


def Columns(
    n: int = 2,
    min_width: str = "100px",
    gap: str = "16px",
    border: str | None = None,
    position: Position = "inline",
    key: str = "",
) -> Tuple[ColumnOutput, ...]:
    """
    Create a responsive row of output columns.

    This helper returns a tuple of `ColumnOutput` widgets (one per column),
    displayed inside a `ColumnsBox`. If the same configuration is executed
    again in the same cell, Mercury reuses the cached instance.

    Parameters
    ----------
    n : int
        Number of columns. Must be >= 1.
        The default is 2.
    min_width : str
        Minimum width for each column (e.g. `"240px"`).
        The default is `"100px"`.
    gap : str
        Gap between columns (e.g. `"16px"`).
        The default is `"16px"`.
    border : str | None
        Border override.
        - If `None`, the value is taken from THEME (`border_visible`, `border_color`).
        - If `""`, borders are disabled.
        - If a CSS string like `"1px solid red"`, that border is applied.
    position : {"sidebar", "inline", "bottom"}
        Controls where the widget is displayed in Mercury layout.
        The default is `"inline"`.
    key : str
        Unique identifier used to differentiate widgets with identical arguments.

    Returns
    -------
    tuple[ColumnOutput, ...]
        A tuple of output widgets you can write into with `with outs[i]: ...`.
    """

    if not isinstance(n, int) or n < 1:
        raise Exception("Columns: `n` must be an integer >= 1.")

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
        # allow updating position on reuse
        box.position = position
        _display_style()
        display(box)
        return outs

    outs = tuple(ColumnOutput() for _ in range(n))

    box = ColumnsBox(
        children=list(outs),
        layout=widgets.Layout(
            width="100%",
            display="flex",
            flex_flow="row wrap",
            gap=gap,
            align_items="stretch",
        ),
        position=position,
    )

    # border resolution
    if border == "":
        border_to_apply = None
    elif border is not None:
        border_to_apply = border
    else:
        # theme-driven
        if THEME.get("border_visible", False):
            border_color = THEME.get("border_color", "lightgray")
            border_to_apply = f"1px solid {border_color}"
        else:
            border_to_apply = None

    for out in outs:
        out.layout.min_width = min_width
        out.layout.flex = "1 1 0px"
        out.add_class("mljar-column")

        if border_to_apply:
            out.layout.border = border_to_apply
            out.layout.padding = "4px"
            out.layout.box_sizing = "border-box"
        else:
            out.layout.border = None

    _display_style()
    display(box)

    WidgetsManager.add_widget(code_uid, (box, outs))
    return outs
