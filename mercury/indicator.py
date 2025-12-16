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
    - Optional delta badge with up/down arrow and color coding
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
          and a negative value shows a downward arrow (red).
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
    BG_GREEN = "rgba(0, 178, 117, 0.12)"
    BG_RED = "rgba(255, 99, 132, 0.13)"

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
              while a negative value shows a downward arrow and red badge.
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
        .mljar-indicator-row {
            width: 100%;
            display: flex;
            flex-direction: row;
            flex-wrap: wrap;                
            gap: 12px;
            justify-content: flex-start;
            align-items: stretch;
            box-sizing: border-box;
            padding: 5px;
        }
        @media (max-width: 800px) {
            .mljar-indicator-row {
                flex-direction: column;
            }
            .mljar-indicator-card {
                flex: 1 1 100%;
                max-width: 100% !important;
                min-width: 0;
            }
        }
        .mljar-indicator-card {
            flex: 0 1 180px;                 
            background: var(--bg, #fff);
            border: 1px solid var(--border, #ebebeb);
            border-radius: 10px;
            padding: 20px 18px 14px 18px;    
            text-align: center;
            min-width: 150px;               
            max-width: 210px !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }
        .mljar-indicator-title {
            font-size: 1.25em !important;
            color: var(--label, #555);
            margin-bottom: 8px;
            font-family: "IBM Plex Sans", system-ui, "Segoe UI", Arial, sans-serif !important;
            font-weight: 500;
            letter-spacing: 0.01em;
        }
        .mljar-indicator-value {
            font-size: 2.3em;                
            color: var(--value, #222);
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
        .mljar-indicator-delta.up {
            background: var(--bg-green, rgba(0,178,117,0.12));
            color: var(--green, #00B275);
        }
        .mljar-indicator-delta.down {
            background: var(--bg-red, rgba(255,99,132,0.13));
            color: var(--red, #FF6384);
        }
        </style>
        """

    def _card_html(self):
        delta_html = ""
        if self.delta is not None:
            try:
                d = float(self.delta)
                up = d > 0
                delta_text = f"<span style='font-size:1.15em'>{'&#8593;' if up else '&#8595;'}</span> {abs(d)}%"
                cls = "mljar-indicator-delta up" if up else "mljar-indicator-delta down"
                delta_html = f"<div class='{cls}'>{delta_text}</div>"
            except Exception:
                delta_html = f"<div class='mljar-indicator-delta'>{self.delta}</div>"

        label_html = f"<div class='mljar-indicator-title'>{self.label}</div>" if self.label else ""
        value_html = f"<div class='mljar-indicator-value'>{self.value}</div>"

        return f"""
<div class="mljar-indicator-card"
     style="--bg:{self.background_color};--border:{self.border_color};--value:{self.value_color};--label:{self.label_color};--green:{self.GREEN};--bg-green:{self.BG_GREEN};--red:{self.RED};--bg-red:{self.BG_RED}">
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
            return f"{self.styles()}<div class='mljar-indicator-row'>{cards}</div>"

        # Single indicator
        return f"{self.styles()}{self._card_html()}"
