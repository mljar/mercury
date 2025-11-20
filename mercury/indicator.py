class Indicator:
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
            font-family: 'Inter', 'Segoe UI', Arial, sans-serif !important;
        }
        .mljar-indicator-value {
            font-size: 2.3em;                
            color: var(--value, #222);
            font-family: 'Menlo', 'Consolas', monospace;
            
            margin-bottom: 10px;
            letter-spacing: 1px;
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
