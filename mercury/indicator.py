from IPython.display import display

from .theme import THEME


class Indicator:
    """
    Visual indicator card for displaying key metrics.

    The `Indicator` class renders a compact, styled card that displays a value,
    an optional label, and an optional delta (change indicator). It is intended
    for dashboards and summary views, such as KPIs, metrics, and status values.

    Indicators can be displayed individually or grouped together by passing
    a list of `Indicator` objects as the `value` of another `Indicator`. In that
    case, they are rendered in a responsive row layout that wraps on smaller
    screens.

    Features
    --------
    - Large, readable value display
    - Optional label (title)
    - Optional delta badge with up/down/neutral color coding
    - Colored top accent bar
    - Predefined variants (primary, success, warning, danger, neutral, ml,
      info, teal, pink, orange)
    - Responsive layout (row → column on small screens)
    - White card background always; color lives in accent bar, border, and badge

    Parameters
    ----------
    value : Any
        Value to display inside the indicator.
        If `value` is a list of `Indicator` instances, they are rendered together
        as a responsive row of indicator cards.
    label : str, optional
        Label displayed above the value.
        Default is ``""``.
    delta : float | str | None, optional
        Optional delta value representing change.

        - If numeric and positive → green badge with ↑
        - If numeric and negative → red badge with ↓
        - If numeric and zero → neutral badge, no arrow
        - If non-numeric → displayed as-is

        Default is ``None``.
    variant : str | None, optional
        Predefined style preset. Sets ``accent_color``, ``border_color``, and
        delta badge colors automatically.

        Semantic variants
            ``"primary"`` (default), ``"success"``, ``"warning"``,
            ``"danger"``, ``"neutral"``

        Domain variants
            ``"ml"``, ``"info"``, ``"teal"``, ``"pink"``, ``"orange"``

        Default is ``"primary"``.
    accent_color : str | None, optional
        Override the top accent bar color. Takes precedence over ``variant``.
        Default is ``None``.
    background_color : str, optional
        Card background color. Default is ``"#ffffff"``.
    border_color : str | None, optional
        Card border color. Takes precedence over ``variant``.
        Default is ``None``.
    value_color : str, optional
        Text color of the main value. Default is ``"#111827"``.
    label_color : str, optional
        Text color of the label. Default is ``"#6b7280"``.

    Examples
    --------
    Single indicator with a variant:

    >>> mr.Indicator(value="98%", label="Accuracy", delta=2.1, variant="success")

    Single indicator with custom accent:

    >>> mr.Indicator(value="$12,340", label="Revenue", delta=3.1, accent_color="#7c3aed")

    Row of indicators:

    >>> mr.Indicator([
    ...     mr.Indicator(value="123",  label="Users",    delta=5.4,  variant="primary"),
    ...     mr.Indicator(value="98%",  label="Accuracy", delta=-1.2, variant="danger"),
    ...     mr.Indicator(value="1.3s", label="Latency",              variant="warning"),
    ...     mr.Indicator(value="0.94", label="AUC",      delta=0.02, variant="ml"),
    ... ])

    Notes
    -----
    - Rendering is done via HTML using the ``_repr_html_`` protocol.
    - Numeric deltas are formatted as percentages (``abs(delta)%``), with
      trailing zeros stripped (e.g. ``5.0%`` → ``5%``).
    - Per-card color overrides (``accent_color``, ``border_color``) always
      take precedence over ``variant``.
    """

    # ------------------------------------------------------------------ #
    # Variant palette                                                       #
    # Each entry: (accent, border, badge_bg, badge_text)                   #
    # Background is always white; value/label colors come from instance    #
    # ------------------------------------------------------------------ #
    VARIANTS = {
        # Semantic
        "primary": ("#0099cc", "#bae0f5", "#e0f2fe", "#0369a1"),
        "success": ("#16a34a", "#bbf7d0", "#dcfce7", "#166534"),
        "warning": ("#d97706", "#fde68a", "#fef3c7", "#92400e"),
        "danger":  ("#dc2626", "#fecaca", "#fee2e2", "#991b1b"),
        "neutral": ("#6b7280", "#e5e7eb", "#f3f4f6", "#374151"),
        # Domain
        "ml":      ("#7c3aed", "#ddd6fe", "#ede9fe", "#5b21b6"),
        "info":    ("#0891b2", "#a5f3fc", "#cffafe", "#0e7490"),
        "teal":    ("#059669", "#99f6e4", "#ccfbf1", "#047857"),
        "pink":    ("#db2777", "#fbcfe8", "#fce7f3", "#9d174d"),
        "orange":  ("#ea580c", "#fed7aa", "#ffedd5", "#c2410c"),
    }

    # Up/down delta badge colors are fixed regardless of variant
    _DELTA_UP_BG   = "#dcfce7"
    _DELTA_UP_FG   = "#166534"
    _DELTA_DOWN_BG = "#fee2e2"
    _DELTA_DOWN_FG = "#991b1b"

    def __init__(
        self,
        value,
        label="",
        delta=None,
        variant="primary",
        accent_color=None,
        background_color="#ffffff",
        border_color=None,
        value_color="#111827",
        label_color="#6b7280",
        display_now=False,
    ):
        self.value            = value
        self.label            = label
        self.delta            = delta
        self.variant          = variant if variant in self.VARIANTS else "primary"
        self.background_color = background_color
        self.value_color      = value_color
        self.label_color      = label_color
        self.position         = None

        # Resolve accent / border from variant, allow explicit override
        v = self.VARIANTS[self.variant]
        self.accent_color = accent_color or v[0]
        self.border_color = border_color or v[1]
        self._badge_bg    = v[2]
        self._badge_fg    = v[3]

        if display_now:
            self.display()

    def display(self):
        display(self)

    # ------------------------------------------------------------------ #
    # Styles (injected once per _repr_html_ call)                          #
    # ------------------------------------------------------------------ #
    def _styles(self):
        return """
<style>
.mljar-ind-wrap {
    width: 100%%;
    container-type: inline-size;
    font-family: %(font_family)s;
}
.mljar-ind-row {
    width: 100%%;
    display: grid;
    grid-template-columns: 1fr;
    gap: 12px;
    box-sizing: border-box;
}
@container (min-width: 480px) {
    .mljar-ind-row { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@container (min-width: 720px) {
    .mljar-ind-row { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
@container (min-width: 960px) {
    .mljar-ind-row { grid-template-columns: repeat(4, minmax(0, 1fr)); }
}
.mljar-ind-card {
    position: relative;
    overflow: hidden;
    border-radius: 10px;
    padding: 18px 20px 16px;
    box-sizing: border-box;
    width: 100%%;
    text-align: left;
    transition: border-color 0.15s, background-color 0.15s;
}
.mljar-ind-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 10px 10px 0 0;
    background: var(--mljar-accent);
}
.mljar-ind-card:hover {
    border-color: var(--mljar-accent) !important;
    background: %(hover_background_color)s;
}
.mljar-ind-card-single {
    max-width: none;
}
@container (min-width: 480px) {
    .mljar-ind-card-single { max-width: 280px; }
}
.mljar-ind-label {
    font-size: 11px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    margin-bottom: 8px;
}
.mljar-ind-value {
    font-size: 28px;
    font-weight: 600;
    letter-spacing: -0.5px;
    line-height: 1;
    margin-bottom: 12px;
}
.mljar-ind-delta {
    display: inline-flex;
    align-items: center;
    gap: 3px;
    padding: 2px 9px;
    font-size: 11px;
    font-weight: 600;
    border-radius: 20px;
    line-height: 1.6;
}
.mljar-ind-arrow { font-size: 10px; line-height: 1; }
</style>""" % {
            "font_family": THEME.get("font_family", '-apple-system, "Segoe UI", system-ui, Arial, sans-serif'),
            "hover_background_color": THEME.get("hover_background_color", "#f8fafc"),
        }

    # ------------------------------------------------------------------ #
    # Delta badge                                                           #
    # ------------------------------------------------------------------ #
    def _delta_html(self):
        if self.delta is None:
            return ""

        try:
            d = float(self.delta)
            raw = abs(d)
            # Strip trailing zeros: 5.0 → "5", 1.20 → "1.2"
            formatted = f"{raw:.1f}".rstrip("0").rstrip(".") + "%"

            if d > 0:
                text = f"<span class='mljar-ind-arrow'>&#8593;</span>{formatted}"
                bg, fg = self._DELTA_UP_BG, self._DELTA_UP_FG
            elif d < 0:
                text = f"<span class='mljar-ind-arrow'>&#8595;</span>{formatted}"
                bg, fg = self._DELTA_DOWN_BG, self._DELTA_DOWN_FG
            else:
                text = "&#8212;&nbsp;0%"
                bg, fg = self._badge_bg, self._badge_fg

        except (TypeError, ValueError):
            # Non-numeric delta: render as-is using variant badge colors
            text = str(self.delta)
            bg, fg = self._badge_bg, self._badge_fg

        return (
            f"<div class='mljar-ind-delta'"
            f" style='background:{bg};color:{fg};'>"
            f"{text}</div>"
        )

    # ------------------------------------------------------------------ #
    # Single card HTML                                                      #
    # ------------------------------------------------------------------ #
    def _card_html(self, single=False):
        label_html = (
            f"<div class='mljar-ind-label' style='color:{self.label_color};'>"
            f"{self.label}</div>"
            if self.label else ""
        )
        value_html = (
            f"<div class='mljar-ind-value' style='color:{self.value_color};'>"
            f"{self.value}</div>"
        )
        card_cls = (
            "mljar-ind-card mljar-ind-card-single" if single else "mljar-ind-card"
        )
        card_style = (
            f"--mljar-accent:{self.accent_color};"
            f"background:{self.background_color};"
            f"border:0.5px solid {self.border_color};"
        )
        return (
            f"<div class='{card_cls}' style='{card_style}'>"
            f"{label_html}{value_html}{self._delta_html()}"
            f"</div>"
        )

    # ------------------------------------------------------------------ #
    # _repr_html_                                                           #
    # ------------------------------------------------------------------ #
    def _repr_html_(self):
        # List of Indicator instances → responsive row
        if isinstance(self.value, list):
            cards = "".join(
                v._card_html()
                for v in self.value
                if isinstance(v, Indicator)
            )
            return (
                f"{self._styles()}"
                f"<div class='mljar-ind-wrap'>"
                f"<div class='mljar-ind-row'>{cards}</div>"
                f"</div>"
            )

        # Single indicator
        return (
            f"{self._styles()}"
            f"<div class='mljar-ind-wrap'>{self._card_html(single=True)}</div>"
        )
