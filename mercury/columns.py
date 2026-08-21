# Copyright MLJAR Sp. z o.o.
# Licensed under the Apache License, Version 2.0 (Apache-2.0)

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal, Tuple

import ipywidgets as widgets
from IPython.display import HTML, display
import traitlets

from .manager import MERCURY_MIMETYPE, WidgetsManager
from .render_context import LayoutContextOutput, LayoutFrame
from .theme import THEME

Position = Literal["sidebar", "inline", "bottom"]
DEFAULT_MIN_WIDTH = "min(260px, 100%)"


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


class ColumnOutput(LayoutContextOutput):
    """Column output widget."""
    pass


def _clear_output_widget(out) -> None:
    out.clear_output(wait=True)
    if hasattr(out, "outputs"):
        out.outputs = ()


def _normalize_columns_spec(n: int | Sequence[float]) -> tuple[int, tuple[float, ...]]:
    if isinstance(n, bool):
        raise Exception("Columns: `n` must be an integer >= 1 or a non-empty list of positive widths.")

    if isinstance(n, int):
        if n < 1:
            raise Exception("Columns: `n` must be an integer >= 1.")
        return n, tuple(1.0 for _ in range(n))

    if isinstance(n, (str, bytes)) or not isinstance(n, Sequence):
        raise Exception("Columns: `n` must be an integer >= 1 or a non-empty list of positive widths.")

    if len(n) == 0:
        raise Exception("Columns: width list must not be empty.")

    weights = []
    for value in n:
        try:
            weight = float(value)
        except Exception:
            raise Exception("Columns: all width values must be numbers.")
        if weight <= 0:
            raise Exception("Columns: all width values must be greater than 0.")
        weights.append(weight)

    return len(weights), tuple(weights)


def Columns(
    n: int | Sequence[float] = 2,
    min_width: str = DEFAULT_MIN_WIDTH,
    gap: str = "16px",
    border: str | None = None,
    position: Position = "inline",
    key: str = "",
    append: bool = False,
) -> Tuple[ColumnOutput, ...]:
    """
    Create a responsive row of output columns.

    This helper returns a tuple of `ColumnOutput` widgets (one per column),
    displayed inside a `ColumnsBox`. If the same configuration is executed
    again in the same cell, Mercury reuses the cached instance.

    Parameters
    ----------
    n : int | list[float] | tuple[float, ...]
        Number of equal-width columns, or a list of proportional column widths.
        For example, ``Columns(2)`` creates two equal columns and
        ``Columns([0.4, 0.6])`` creates two columns with a 40/60 width ratio.
        The default is 2.
    min_width : str
        Minimum width for each column (e.g. `"240px"`). Columns wrap when
        there is not enough room. By default, columns target a minimum width
        of 260px while remaining constrained to narrow parent containers.
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
    append : bool
        If `False`, clear reused column outputs before writing new content.
        If `True`, preserve previous content and append new output.
        The default is `False`.

    Returns
    -------
    tuple[ColumnOutput, ...]
        A tuple of output widgets you can write into with `with outs[i]: ...`.
    """

    column_count, column_weights = _normalize_columns_spec(n)

    kwargs = {
        "n": column_count,
        "widths": column_weights,
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
        if not append:
            for out in outs:
                _clear_output_widget(out)
        _display_style()
        display(box)
        return outs

    outs = tuple(
        ColumnOutput(
            layout_frame=LayoutFrame(
                layout_type="columns",
                owner_id=code_uid,
                slot_key=str(i),
            )
        )
        for i in range(column_count)
    )

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
    box.add_class("mljar-columns")

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

    for out, weight in zip(outs, column_weights):
        out.layout.min_width = min_width
        out.layout.max_width = "100%"
        out.layout.box_sizing = "border-box"
        out.layout.flex = f"{weight:g} 1 0px"
        out.add_class("mljar-column")

        if border_to_apply:
            out.layout.border = border_to_apply
            out.layout.padding = "4px"
        else:
            out.layout.border = None

    _display_style()
    display(box)

    WidgetsManager.add_widget(code_uid, (box, outs))
    return outs
