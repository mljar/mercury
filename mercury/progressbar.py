import ipywidgets as widgets
import traitlets
from IPython.display import display

from .manager import WidgetsManager, MERCURY_MIMETYPE
from .theme import THEME


# ---------- Global CSS ----------
def _ensure_global_progress_styles():
    css = f"""
    <style>
      .mljar-progress {{
        width: 100%;
        display: flex;
        flex-direction: column;
        gap: 0px;
        box-sizing: border-box;
      }}

      .mljar-progress-label {{
        font-family: {THEME.get('font_family', 'Arial, sans-serif')};
        font-size: {THEME.get('font_size', '14px')};
        color: {THEME.get('text_color', '#222')};
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0px;
        margin-top: 0px !important;
        margin-bottom: 0px !important;
        padding-top: 0px !important;      /* fixed: paddding-top -> padding-top */
        padding-bottom: 0px !important;
        line-height: 0.7; 
      }}

      .mljar-progress-track {{
        width: 100%;
        height: 12px;
        background: {THEME.get('panel_bg_hover', '#f5f5f7')};
        border: 1px solid {THEME.get('border_color', '#ddd')};
        border-radius: {THEME.get('border_radius', '8px')};
        overflow: hidden;
        position: relative;
        box-sizing: border-box;
      }}

      .mljar-progress-fill {{
        height: 100%;
        background: linear-gradient(
          90deg,
          {THEME.get('primary_color', '#007bff')} 0%,
          {THEME.get('primary_color', '#007bff')} 100%
        );
        border-radius: inherit;
        transition: width 200ms ease;
        will-change: width;
      }}

      .mljar-progress-fill.is-indeterminate {{
        width: 30%;
        background: repeating-linear-gradient(
          45deg,
          {THEME.get('primary_color', '#007bff')} 0 10px,
          rgba(255,255,255,0.35) 10px 20px
        );
        animation: mljar-progress-stripes 1.0s linear infinite;
        opacity: 0.95;
      }}

      @keyframes mljar-progress-stripes {{
        0% {{ transform: translateX(-100%); }}
        100% {{ transform: translateX(300%); }}
      }}

      .mljar-progress :is(.jupyter-widgets, .widget-box, .widget-hbox, .widget-vbox) {{
        margin-left: 0 !important;
        margin-right: 0 !important;
        max-width: 100%;
        box-sizing: border-box;
      }}
    </style>
    """
    display(widgets.HTML(css))


# ---------- Container that carries "position" and emits Mercury MIME ----------
class _ProgressVBox(widgets.VBox):
    position = traitlets.Enum(
        values=["sidebar", "inline", "bottom"],
        default_value="inline"
    ).tag(sync=True)

    def _repr_mimebundle_(self, **kwargs):
        data = super()._repr_mimebundle_(**kwargs)
        # ipywidgets usually returns a dict; handle both dict and (rare) tuple(data, metadata)
        if isinstance(data, dict):
            data[MERCURY_MIMETYPE] = {
                "widget": type(self).__qualname__,
                "model_id": getattr(self, "model_id", None),
                "position": self.position,
            }
        elif isinstance(data, tuple) and len(data) >= 1 and isinstance(data[0], dict):
            bundle = data[0]
            bundle[MERCURY_MIMETYPE] = {
                "widget": type(self).__qualname__,
                "model_id": getattr(self, "model_id", None),
                "position": self.position,
            }
        return data


# ---------- Handle returned to the caller ----------
class ProgressHandle:
    """Simple controller for the Progress widget."""
    def __init__(self, container, label_w, percent_w, fill_w, min_v, max_v, indeterminate):
        self._container = container
        self._label_w = label_w
        self._percent_w = percent_w
        self._fill_w = fill_w
        self._min = min_v
        self._max = max_v
        self._indeterminate = indeterminate

    def set(self, value: float):
        """Set determinate value; switches off indeterminate mode if enabled."""
        self.set_indeterminate(False)
        clamped = max(self._min, min(self._max, float(value)))
        pct = 0 if self._max == self._min else (clamped - self._min) / (self._max - self._min) * 100.0
        self._fill_w.layout.width = f"{pct:.2f}%"
        if self._percent_w is not None:
            self._percent_w.value = f"{pct:.0f}%"

    def set_label(self, text: str):
        if self._label_w is not None:
            self._label_w.value = text

    def set_indeterminate(self, on: bool = True):
        if on and not self._indeterminate:
            self._fill_w.add_class("is-indeterminate")
            self._fill_w.layout.width = "30%"
            self._indeterminate = True
            if self._percent_w is not None:
                self._percent_w.value = ""
        elif not on and self._indeterminate:
            self._fill_w.remove_class("is-indeterminate")
            self._indeterminate = False

    def show(self):
        display(self._container)

    def hide(self):
        self._container.layout.display = "none"

    def show_inline(self):
        self._container.layout.display = ""


# ---------- Public factory ----------
def ProgressBar(
    label: str = "",
    value: float = 0,
    min: float = 0,
    max: float = 100,
    show_percent: bool = True,
    indeterminate: bool = False,
    key: str = "",
    position: str = "inline",
) -> ProgressHandle:
    """
    Create and display a theme-aware progress bar.

    This function renders a progress bar widget that can operate in either
    determinate mode (percentage-based) or indeterminate mode (animated).
    A `ProgressHandle` is returned to allow dynamic updates to the progress
    after rendering.

    The widget integrates with Mercury layout management and supports
    placement in the main view, sidebar, or bottom area.

    Parameters
    ----------
    label : str, optional
        Optional text shown above the progress bar.
        Default is `""`.
    value : float, optional
        Initial value for determinate mode.
        The value is clamped to the `[min, max]` range.
        Default is `0`.
    min : float, optional
        Minimum value for determinate mode.
        Default is `0`.
    max : float, optional
        Maximum value for determinate mode.
        Default is `100`.
    show_percent : bool, optional
        If `True`, display the percentage value aligned to the right
        of the label row.
        Default is `True`.
    indeterminate : bool, optional
        If `True`, the progress bar starts in indeterminate (animated) mode.
        In this mode, the percentage text is hidden.
        Default is `False`.
    key : str, optional
        Stable cache key used to reuse the same widget instance
        across multiple executions.
    position : {"sidebar", "inline", "bottom"}, optional
        Placement hint for Mercury/JupyterLab integration.
        Default is `"inline"`.

    Returns
    -------
    ProgressHandle
        A controller object used to update and control the progress bar.

    Examples
    --------
    Basic determinate progress:

    >>> import mercury as mr
    >>> p = mr.ProgressBar(label="Training", value=0)
    >>> p.set(30)
    >>> p.set(75)
    >>> p.set(100)

    Indeterminate progress:

    >>> p = mr.ProgressBar(label="Loading", indeterminate=True)
    >>> # do some work...
    >>> p.set_indeterminate(False)
    >>> p.set(100)

    Dynamic label update:

    >>> p = mr.ProgressBar(label="Step 1/3")
    >>> p.set_label("Step 2/3")

    Notes
    -----
    - Indeterminate mode is useful when progress cannot be measured.
    - Determinate mode automatically disables indeterminate animation.
    - The progress bar is rendered immediately when the function is called.
    """

    _ensure_global_progress_styles()

    code_uid = WidgetsManager.get_code_uid("Progress", key=key or label or "progress",
                    kwargs=dict(label=label, min=min, max=max, show_percent=show_percent,
                    indeterminate=indeterminate))
    cached = WidgetsManager.get_widget(code_uid)
    if cached:
        container, handle = cached
        display(container)
        return handle

    # Label row
    label_w = widgets.HTML(label) if label else None
    percent_w = widgets.HTML("") if show_percent else None
    if show_percent:
        label_row = widgets.HBox(
            [
                label_w if label_w else widgets.HTML(""),
                widgets.HBox([percent_w], layout=widgets.Layout(flex="0 0 auto"))
            ],
            layout=widgets.Layout(width="100%", align_items="center", justify_content="space-between")
        )
    else:
        label_row = widgets.HBox(
            [label_w] if label_w else [],
            layout=widgets.Layout(width="100%", align_items="center", justify_content="space-between")
        )
    label_row.add_class("mljar-progress-label")

    # Track + fill
    fill_w = widgets.Box(layout=widgets.Layout(width="0%", height="100%"))
    fill_w.add_class("mljar-progress-fill")

    track_w = widgets.Box([fill_w], layout=widgets.Layout(width="100%", height="12px"))
    track_w.add_class("mljar-progress-track")

    # Container with position support
    parts = [label_row, track_w] if (label or show_percent) else [track_w]
    container = _ProgressVBox(parts, layout=widgets.Layout(width="100%"))
    container.position = position
    container.add_class("mljar-progress")

    # Compose handle
    handle = ProgressHandle(
        container=container,
        label_w=label_w,
        percent_w=percent_w,
        fill_w=fill_w,
        min_v=float(min),
        max_v=float(max),
        indeterminate=bool(indeterminate),
    )

    # Initialize
    if indeterminate:
        handle.set_indeterminate(True)
    else:
        handle.set(value)

    display(container)
    WidgetsManager.add_widget(code_uid, (container, handle))
    return handle
