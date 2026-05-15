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
    - Responsive layout (row → column on small screens)
    - Theme-friendly styling via CSS variables

    Parameters
    ----------
    value : Any
        Value to display inside the indicator.
        If `value` is a list of `Indicator` instances, they are rendered together
        as a responsive row of indicator cards.
    label : str, optional
        Label displayed above the value.
        Default is `""`.
    delta : float | str | None, optional
        Optional delta value representing change.
        - If numeric, a positive value shows an upward arrow (green),
          a negative value shows a downward arrow (red),
          and zero is rendered as neutral.
        - If non-numeric, the value is displayed as-is.
        Default is `None`.
    background_color : str, optional
        Background color of the indicator card.
        Default is `"#fff"`.
    border_color : str, optional
        Border color of the indicator card.
        Default is `"#ebebeb"`.
    value_color : str, optional
        Text color of the main value.
        Default is `"#222"`.
    label_color : str, optional
        Text color of the label.
        Default is `"#555"`.

    Examples
    --------
    Display a single indicator:

    >>> mr.Indicator(
    ...     value="123",
    ...     label="Users",
    ...     delta=5.4
    ... )

    Display multiple indicators in one row:

    >>> mr.Indicator([
    ...     mr.Indicator(value="123", label="Users", delta=5.4),
    ...     mr.Indicator(value="98%", label="Accuracy", delta=-1.2),
    ...     mr.Indicator(value="1.3s", label="Latency")
    ... ])

    Notes
    -----
    - Rendering is done via HTML and CSS using the `_repr_html_` protocol.
    - Delta colors and arrows are determined automatically for numeric values.
    - The layout is responsive and adapts to smaller screen sizes.
    """

    GREEN = "#00B275"
    RED = "#FF6384"
    NEUTRAL = "#6B7280"
    BG_GREEN = "rgba(0, 178, 117, 0.12)"
    BG_RED = "rgba(255, 99, 132, 0.13)"
    BG_NEUTRAL = "rgba(107, 114, 128, 0.12)"

    def __init__(
        self,
        value,
        label="",
        delta=None,
        background_color="#fff",
        border_color="#ebebeb",
        value_color="#222",
        label_color="#555"
    ):
        """
        Create a single indicator card.

        Parameters
        ----------
        value : Any
            Main value displayed in the indicator.
            Can be a string, number, or any object convertible to string.
            If `value` is a list of `Indicator` instances, they are rendered
            together as a responsive row of indicator cards.
        label : str, optional
            Optional label displayed above the value.
            Default is `""`.
        delta : float | str | None, optional
            Optional delta (change) value.

            - If numeric, a positive value shows an upward arrow and green badge,
              a negative value shows a downward arrow and red badge,
              and zero shows a neutral badge without an arrow.
            - If non-numeric, the value is displayed without arrow logic.
            Default is `None`.
        background_color : str, optional
            Background color of the indicator card.
            Default is `"#fff"`.
        border_color : str, optional
            Border color of the indicator card.
            Default is `"#ebebeb"`.
        value_color : str, optional
            Text color of the main value.
            Default is `"#222"`.
        label_color : str, optional
            Text color of the label.
            Default is `"#555"`.
        """
        self.value = value
        self.label = label
        self.delta = delta
        self.background_color = background_color
        self.border_color = border_color
        self.value_color = value_color
        self.label_color = label_color
        self.position = None

    def styles(self):
        return """
        <style scoped>
        .mljar-indicator-container {
            width: 100%;
            container-type: inline-size;
        }
        .mljar-indicator-row {
            width: 100%;
            display: grid;
            grid-template-columns: 1fr;
            gap: 12px;
            box-sizing: border-box;
        }
        @container (min-width: 560px) {
            .mljar-indicator-row {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }
        @container (min-width: 900px) {
            .mljar-indicator-row {
                grid-template-columns: repeat(3, minmax(0, 1fr));
            }
        }
        @container (min-width: 1150px) {
            .mljar-indicator-row {
                grid-template-columns: repeat(4, minmax(0, 1fr));
            }
        }
        .mljar-indicator-card {
            border-radius: 10px;
            padding: 20px 18px 14px 18px;    
            text-align: center;
            width: 100%;
            min-width: 0;
            max-width: none !important;
            box-sizing: border-box;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }
        .mljar-indicator-card-single {
            max-width: none !important;
        }
        @container (min-width: 480px) {
            .mljar-indicator-card-single {
                max-width: 400px !important;
                margin-left: auto;
                margin-right: auto;
            }
        }
        .mljar-indicator-title {
            font-size: 1.25em !important;
            margin-bottom: 8px;
            font-family: "IBM Plex Sans", system-ui, "Segoe UI", Arial, sans-serif !important;
            font-weight: 500;
            letter-spacing: 0.01em;
        }
        .mljar-indicator-value {
            font-size: 2.3em;                
            font-family: 'Menlo', 'Consolas', monospace;
            
            margin-bottom: 10px;
            letter-spacing: 1px;
            font-weight: 600;
        }
        .mljar-indicator-delta {
            display: inline-block;
            padding: 0.24em 1em 0.24em 1em;
            font-size: 0.95em;
            border-radius: 2em;
            margin-bottom: 4px;
            font-family: 'Menlo', monospace;
            font-weight: bold;
        }
        </style>
        """

    def _card_html(self, single=False):
        delta_html = ""
        if self.delta is not None:
            try:
                d = float(self.delta)
                if d > 0:
                    delta_text = (
                        f"<span style='font-size:1.15em'>&#8593;</span> {abs(d)}%"
                    )
                    delta_style = (
                        f"background:{self.BG_GREEN};color:{self.GREEN};"
                    )
                elif d < 0:
                    delta_text = (
                        f"<span style='font-size:1.15em'>&#8595;</span> {abs(d)}%"
                    )
                    delta_style = (
                        f"background:{self.BG_RED};color:{self.RED};"
                    )
                else:
                    delta_text = "0%"
                    delta_style = (
                        f"background:{self.BG_NEUTRAL};color:{self.NEUTRAL};"
                    )
                delta_html = (
                    f"<div class='mljar-indicator-delta' style='{delta_style}'>"
                    f"{delta_text}</div>"
                )
            except Exception:
                delta_html = f"<div class='mljar-indicator-delta'>{self.delta}</div>"

        label_html = (
            f"<div class='mljar-indicator-title' style='color:{self.label_color}'>"
            f"{self.label}</div>"
            if self.label
            else ""
        )
        value_html = (
            f"<div class='mljar-indicator-value' style='color:{self.value_color}'>"
            f"{self.value}</div>"
        )
        card_cls = "mljar-indicator-card mljar-indicator-card-single" if single else "mljar-indicator-card"

        return f"""
<div class="{card_cls}"
     style="background:{self.background_color};border:1px solid {self.border_color};">
    {label_html}
    {value_html}
    {delta_html}
</div>
"""

    def _repr_html_(self):
        # List of indicators -> one row that wraps
        if isinstance(self.value, list):
            cards = ""
            for v in self.value:
                if isinstance(v, Indicator):
                    cards += v._card_html()
            return f"{self.styles()}<div class='mljar-indicator-container'><div class='mljar-indicator-row'>{cards}</div></div>"

        # Single indicator
        return f"{self.styles()}<div class='mljar-indicator-container'>{self._card_html(single=True)}</div>"
