import math
from collections.abc import Mapping
from html import escape
from numbers import Real

import pandas as pd
from IPython.display import display

from .theme import THEME


_CHART_WIDTH = 440.0
_CENTER_X = 244.0
_LABEL_X = 500.0
_TOP_MARGIN = 24.0
_BOTTOM_MARGIN = 24.0
_STAGE_HEIGHT = 70.0
_STAGE_GAP = 4.0
_MINIMUM_STAGE_HEIGHT = 40.0
_MINIMUM_POSITIVE_WIDTH = 6.0


def _normalize_stage(raw):
    if not pd.api.types.is_scalar(raw) or pd.isna(raw):
        raise ValueError("Funnel stage names cannot be empty.")
    stage = str(raw).strip()
    if not stage:
        raise ValueError("Funnel stage names cannot be empty.")
    return stage


def _normalize_value(raw):
    if pd.api.types.is_bool(raw) or isinstance(raw, (str, bytes)):
        raise ValueError("Funnel values must be numeric.")
    try:
        value = float(raw)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("Funnel values must be numeric.") from error
    if not math.isfinite(value):
        raise ValueError("Funnel values must be finite; NaN and infinity are unsupported.")
    if value < 0:
        raise ValueError("Funnel values cannot be negative.")
    return value


def _input_rows(data, stage, value):
    if isinstance(data, pd.DataFrame):
        for column, role in ((stage, "stage"), (value, "value")):
            if column not in data.columns:
                raise ValueError(f"Funnel {role} column '{column}' was not found.")
        return data[[stage, value]].itertuples(index=False, name=None)

    if isinstance(data, Mapping):
        return data.items()

    if not isinstance(data, (list, tuple)):
        raise TypeError(
            "Funnel data must be a pandas DataFrame, dictionary, or a list of "
            "tuples or dictionaries."
        )

    rows = []
    for index, row in enumerate(data):
        if isinstance(row, Mapping):
            missing = [key for key in (stage, value) if key not in row]
            if missing:
                raise ValueError(
                    f"Funnel row {index} is missing required key '{missing[0]}'."
                )
            rows.append((row[stage], row[value]))
        elif isinstance(row, (list, tuple)) and len(row) == 2:
            rows.append(tuple(row))
        else:
            raise ValueError(
                f"Funnel row {index} must be a two-item tuple or dictionary."
            )
    return rows


def _normalize_data(data, stage="stage", value="value"):
    stages = [
        {"stage": _normalize_stage(raw_stage), "value": _normalize_value(raw_value)}
        for raw_stage, raw_value in _input_rows(data, stage, value)
    ]
    if not stages:
        raise ValueError("Funnel requires at least one stage.")
    return stages


def _calculate_percentages(stages, mode="previous"):
    if mode not in {"previous", "first"}:
        raise ValueError("Funnel percentage must be 'previous' or 'first'.")

    percentages = [100.0]
    for index in range(1, len(stages)):
        denominator = stages[index - 1]["value"] if mode == "previous" else stages[0]["value"]
        percentages.append(
            None
            if denominator == 0
            else stages[index]["value"] / denominator * 100
        )
    return percentages


def _format_value(value, value_format=","):
    rendered = int(value) if float(value).is_integer() else value
    if value_format is None:
        return str(rendered)
    try:
        return format(rendered, value_format)
    except (TypeError, ValueError) as error:
        raise ValueError(f"Funnel value_format '{value_format}' is not valid.") from error


def _format_percentage(value):
    if value is None:
        return "—"
    rounded = round(value, 1)
    if rounded.is_integer():
        return f"{int(rounded)}%"
    return f"{rounded:.1f}%"


def _resolve_height(stage_count, height):
    gaps = _STAGE_GAP * max(0, stage_count - 1)
    if height is None:
        return _TOP_MARGIN + _BOTTOM_MARGIN + stage_count * _STAGE_HEIGHT + gaps
    if isinstance(height, bool) or not isinstance(height, Real):
        raise ValueError("Funnel height must be numeric or None.")
    height = float(height)
    minimum = (
        _TOP_MARGIN
        + _BOTTOM_MARGIN
        + stage_count * _MINIMUM_STAGE_HEIGHT
        + gaps
    )
    if not math.isfinite(height) or height < minimum:
        raise ValueError(
            f"Funnel height must be at least {minimum:g} for {stage_count} stages."
        )
    return height


def _calculate_layout(stages, height=None):
    svg_height = _resolve_height(len(stages), height)
    gaps = _STAGE_GAP * max(0, len(stages) - 1)
    stage_height = (
        svg_height - _TOP_MARGIN - _BOTTOM_MARGIN - gaps
    ) / len(stages)
    max_value = max(item["value"] for item in stages)

    def scaled_width(value):
        if value == 0 or max_value == 0:
            return 0.0
        return max(_MINIMUM_POSITIVE_WIDTH, value / max_value * _CHART_WIDTH)

    widths = [scaled_width(item["value"]) for item in stages]
    layout = []
    for index, item in enumerate(stages):
        top_width = widths[index]
        bottom_width = widths[index + 1] if index + 1 < len(stages) else top_width
        y = _TOP_MARGIN + index * (stage_height + _STAGE_GAP)
        layout.append(
            {
                **item,
                "x1": _CENTER_X - top_width / 2,
                "x2": _CENTER_X + top_width / 2,
                "x3": _CENTER_X + bottom_width / 2,
                "x4": _CENTER_X - bottom_width / 2,
                "y1": y,
                "y2": y + stage_height,
                "top_width": top_width,
                "bottom_width": bottom_width,
                "label_y": y + stage_height / 2,
                "connector_x": _CENTER_X + (top_width + bottom_width) / 4,
            }
        )
    return layout, svg_height


def _parse_hex_color(raw):
    if not isinstance(raw, str):
        return None
    color = raw.strip()
    if not color.startswith("#"):
        return None
    digits = color[1:]
    if len(digits) == 3:
        digits = "".join(character * 2 for character in digits)
    if len(digits) != 6:
        return None
    try:
        int(digits, 16)
    except ValueError:
        return None
    return f"#{digits.lower()}"


def _mix_colors(foreground, background, ratio):
    foreground = _parse_hex_color(foreground)
    background = _parse_hex_color(background)
    if foreground is None or background is None:
        return foreground or background or "#007bff"
    first = tuple(int(foreground[index : index + 2], 16) for index in (1, 3, 5))
    second = tuple(int(background[index : index + 2], 16) for index in (1, 3, 5))
    mixed = tuple(
        round(a * ratio + b * (1 - ratio)) for a, b in zip(first, second)
    )
    return "#{:02x}{:02x}{:02x}".format(*mixed)


def _resolve_colors(stages, colors):
    primary = THEME.get("primary_color", "#007bff")
    surface = THEME.get("surface_color", "#ffffff")
    count = len(stages)
    ratios = [0.9 if count == 1 else 0.9 - index * 0.4 / (count - 1) for index in range(count)]
    defaults = [_mix_colors(primary, surface, ratio) for ratio in ratios]

    if colors is None:
        return defaults
    if isinstance(colors, Mapping):
        mapping = {}
        for raw_stage, raw_color in colors.items():
            stage = _normalize_stage(raw_stage)
            color = _parse_hex_color(raw_color)
            if color is None:
                raise ValueError("Funnel colors must be #RGB or #RRGGBB hex values.")
            mapping[stage] = color
        return [mapping.get(item["stage"], defaults[index]) for index, item in enumerate(stages)]
    if not isinstance(colors, (list, tuple)) or not colors:
        raise ValueError("Funnel colors must be a non-empty list, dictionary, or None.")
    palette = []
    for raw_color in colors:
        color = _parse_hex_color(raw_color)
        if color is None:
            raise ValueError("Funnel colors must be #RGB or #RRGGBB hex values.")
        palette.append(color)
    return [palette[index % len(palette)] for index in range(count)]


def _number(value):
    return f"{value:.3f}".rstrip("0").rstrip(".")


class Funnel:
    """Display prepared stage-value data as a responsive SVG funnel chart.

    Parameters
    ----------
    data : pandas.DataFrame, dict, or list
        Ordered stage-value rows supplied as a DataFrame, mapping, two-item
        tuples, or row dictionaries.
    stage, value : str, optional
        DataFrame column names or row-dictionary keys. Defaults are
        ``"stage"`` and ``"value"``.
    colors : list[str] or dict[str, str] or None, optional
        Hex stage colors. Lists cycle through stages; dictionaries map stage
        names. Coordinated Mercury theme shades are used by default.
    height : int, float, or None, optional
        SVG view-box height. It is calculated from the number of stages when
        omitted.
    show_values : bool, optional
        Display formatted stage values. Default is ``True``.
    show_percentage : bool, optional
        Display conversion percentages. Default is ``True``.
    percentage : {"previous", "first"}, optional
        Compare each stage with the previous or first stage. Default is
        ``"previous"``.
    value_format : str or None, optional
        Python numeric format specification. Default is ``","``.

    Notes
    -----
    Stage order is preserved. Values may increase and zero values are valid.
    Rendering uses only HTML and SVG, with no JavaScript dependency.
    """

    def __init__(
        self,
        data,
        stage="stage",
        value="value",
        colors=None,
        height=None,
        show_values=True,
        show_percentage=True,
        percentage="previous",
        value_format=",",
    ):
        if value_format is not None and not isinstance(value_format, str):
            raise ValueError("Funnel value_format must be a string or None.")
        if value_format is not None:
            _format_value(1.0, value_format)

        self.stages = _normalize_data(data, stage, value)
        self.show_values = bool(show_values)
        self.show_percentage = bool(show_percentage)
        self.percentage = percentage
        self.value_format = value_format
        self.percentages = _calculate_percentages(self.stages, percentage)
        self.layout, self.height = _calculate_layout(self.stages, height)
        self.colors = _resolve_colors(self.stages, colors)
        longest_label = max(len(item["stage"]) for item in self.stages)
        self.width = max(700.0, _LABEL_X + longest_label * 7.2 + 28.0)

    def _styles(self):
        return """
<style>
.mljar-funnel {
    width: 100%%;
    max-width: 100%%;
    overflow-x: auto;
    color: %(text_color)s;
    font-family: %(font_family)s;
}
.mljar-funnel-svg {
    display: block;
    width: 100%%;
    min-width: 520px;
    height: auto;
}
.mljar-funnel-stage {
    stroke: %(surface_color)s;
    stroke-width: 1;
}
.mljar-funnel-connector {
    stroke: %(border_color)s;
    stroke-width: 1;
}
.mljar-funnel-stage-label {
    fill: %(text_color)s;
    font-size: 14px;
    font-weight: 600;
}
.mljar-funnel-meta-label {
    fill: %(muted_text_color)s;
    font-size: 12px;
}
</style>""" % {
            "font_family": THEME.get("font_family", "Arial, sans-serif"),
            "text_color": THEME.get("text_color", "#0f172a"),
            "muted_text_color": THEME.get("muted_text_color", "#6b7280"),
            "surface_color": THEME.get("surface_color", "#ffffff"),
            "border_color": THEME.get("border_color", "#d0d7de"),
        }

    def _tooltip(self, index):
        item = self.stages[index]
        tooltip = f"{item['stage']}: {_format_value(item['value'], self.value_format)}"
        if index > 0 and self.show_percentage:
            relation = "previous stage" if self.percentage == "previous" else "first stage"
            tooltip += f" — {_format_percentage(self.percentages[index])} of {relation}"
        return tooltip

    def _stage_svg(self, index):
        geometry = self.layout[index]
        tooltip = self._tooltip(index)
        points = " ".join(
            (
                f"{_number(geometry['x1'])},{_number(geometry['y1'])}",
                f"{_number(geometry['x2'])},{_number(geometry['y1'])}",
                f"{_number(geometry['x3'])},{_number(geometry['y2'])}",
                f"{_number(geometry['x4'])},{_number(geometry['y2'])}",
            )
        )
        metadata = []
        if self.show_values:
            metadata.append(_format_value(geometry["value"], self.value_format))
        if self.show_percentage:
            metadata.append(_format_percentage(self.percentages[index]))
        has_metadata = bool(metadata)
        stage_y = geometry["label_y"] - 5 if has_metadata else geometry["label_y"]
        baseline = "auto" if has_metadata else "middle"
        meta_svg = ""
        if has_metadata:
            meta_svg = (
                f'<text class="mljar-funnel-meta-label" x="{_number(_LABEL_X)}" '
                f'y="{_number(geometry["label_y"] + 13)}">'
                f"{escape(' · '.join(metadata))}</text>"
            )
        return (
            f'<g class="mljar-funnel-stage-group" role="img" '
            f'aria-label="{escape(tooltip, quote=True)}"><title>{escape(tooltip)}</title>'
            f'<polygon class="mljar-funnel-stage" points="{points}" '
            f'fill="{self.colors[index]}" />'
            f'<line class="mljar-funnel-connector" '
            f'x1="{_number(geometry["connector_x"])}" '
            f'y1="{_number(geometry["label_y"])}" x2="{_number(_LABEL_X - 10)}" '
            f'y2="{_number(geometry["label_y"])}" />'
            f'<text class="mljar-funnel-stage-label" x="{_number(_LABEL_X)}" '
            f'y="{_number(stage_y)}" dominant-baseline="{baseline}">'
            f'{escape(geometry["stage"])}</text>{meta_svg}</g>'
        )

    def display(self):
        display(self)

    def _repr_html_(self):
        stages = "".join(self._stage_svg(index) for index in range(len(self.stages)))
        aria_label = f"Funnel chart with {len(self.stages)} stages"
        svg = (
            f'<svg class="mljar-funnel-svg" '
            f'viewBox="0 0 {_number(self.width)} {_number(self.height)}" '
            f'role="img" aria-label="{aria_label}" '
            f'xmlns="http://www.w3.org/2000/svg">'
            "<title>Funnel chart</title>"
            f"<desc>{aria_label}. Stage width represents its value.</desc>"
            f"{stages}</svg>"
        )
        return f'{self._styles()}<div class="mljar-funnel">{svg}</div>'
