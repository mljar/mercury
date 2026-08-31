import math
from html import escape
from numbers import Integral, Real

import pandas as pd
from IPython.display import display
from pandas.api.types import is_bool_dtype, is_numeric_dtype

from .theme import THEME


class ActivityCalendar:
    """Display prepared daily numeric data as a GitHub-style calendar.

    Parameters
    ----------
    data : pandas.DataFrame
        Prepared data containing at most one numeric value for each day.
    date : str, optional
        Name of the date column. Default is ``"date"``.
    value : str, optional
        Name of the numeric value column. Default is ``"value"``.
    title : str or None, optional
        Heading displayed above the calendar.
    unit : str or None, optional
        Unit appended to active-day tooltips and displayed by the legend.
    color : str or None, optional
        Strongest activity color. Use ``"green"``, ``"red"``, or a hex color.
        Lower intensity colors are generated automatically. Green is the default.
    start_date, end_date : date-like or None, optional
        Inclusive calendar boundaries. Data boundaries are used when omitted.
    levels : int, optional
        Total number of intensity levels, including inactive. Default is ``5``.
    show_legend : bool, optional
        Whether to render the intensity legend.
    show_weekdays : bool, optional
        Whether to render weekday labels.
    show_months : bool, optional
        Whether to render month labels.

    Notes
    -----
    Dates are normalized to calendar days. Duplicate dates are rejected rather
    than aggregated. Missing dates and non-positive values are inactive.
    """

    _CELL_SIZE = 11
    _CELL_GAP = 3
    _WEEKDAY_LABEL_WIDTH = 32
    _MONTH_LABEL_HEIGHT = 20
    _MULTI_YEAR_WEEK_COUNT = 54
    _COLOR_PRESETS = {
        "green": "success_color",
        "red": "danger_color",
    }

    def __init__(
        self,
        data,
        date="date",
        value="value",
        title=None,
        unit=None,
        color=None,
        start_date=None,
        end_date=None,
        levels=5,
        show_legend=True,
        show_weekdays=True,
        show_months=True,
    ):
        if not isinstance(data, pd.DataFrame):
            raise TypeError("ActivityCalendar requires data to be a pandas DataFrame.")
        if data.empty:
            raise ValueError("ActivityCalendar requires a non-empty DataFrame.")
        if date not in data.columns:
            raise ValueError(f"ActivityCalendar date column '{date}' was not found.")
        if value not in data.columns:
            raise ValueError(f"ActivityCalendar value column '{value}' was not found.")
        if isinstance(levels, bool) or not isinstance(levels, Integral) or levels < 2:
            raise ValueError(
                "ActivityCalendar levels must be an integer greater than or equal to 2."
            )
        if is_bool_dtype(data[value].dtype) or not is_numeric_dtype(data[value].dtype):
            raise ValueError(
                f"ActivityCalendar value column '{value}' must contain numeric values."
            )

        dates = self._normalize_dates(data[date], f"column '{date}'")
        if dates.duplicated().any():
            raise ValueError(
                "ActivityCalendar requires one value per day.\n"
                "Aggregate duplicate dates before passing the DataFrame."
            )

        values = data[value].reset_index(drop=True)
        for item in values.dropna():
            try:
                finite = math.isfinite(float(item))
            except (TypeError, ValueError, OverflowError):
                finite = False
            if not finite:
                raise ValueError(
                    f"ActivityCalendar value column '{value}' must contain finite "
                    "numeric values."
                )

        first_date = dates.min()
        last_date = dates.max()
        resolved_start = (
            first_date
            if start_date is None
            else self._normalize_boundary(start_date, "start_date")
        )
        resolved_end = (
            last_date
            if end_date is None
            else self._normalize_boundary(end_date, "end_date")
        )
        if resolved_start > resolved_end:
            raise ValueError(
                "ActivityCalendar start_date must be before or equal to end_date."
            )

        self.data = data.copy()
        self.date = date
        self.value = value
        self.title = title
        self.unit = unit
        self.color = color
        self.start_date = resolved_start
        self.end_date = resolved_end
        self.levels = int(levels)
        self.show_legend = bool(show_legend)
        self.show_weekdays = bool(show_weekdays)
        self.show_months = bool(show_months)
        self._values = dict(zip(dates, values))
        self._days = pd.date_range(self.start_date, self.end_date, freq="D")

        positive_values = [
            float(self._values[day])
            for day in self._days
            if day in self._values
            and not pd.isna(self._values[day])
            and float(self._values[day]) > 0
        ]
        self._max_value = max(positive_values, default=0.0)
        self._inactive_color = THEME.get("panel_bg_hover_2", "#eef2f7")
        self._surface_color = THEME.get("surface_color", "#ffffff")
        self._strongest_color = self._resolve_color(color)
        self._active_colors = [
            self._mix_colors(
                self._strongest_color,
                self._surface_color,
                level / (self.levels - 1),
            )
            for level in range(1, self.levels)
        ]

    @staticmethod
    def _normalize_dates(values, label):
        try:
            parsed = pd.to_datetime(values, errors="raise")
            normalized = pd.DatetimeIndex(
                [pd.Timestamp(item).tz_localize(None).normalize() for item in parsed]
            )
        except (TypeError, ValueError, OverflowError) as error:
            raise ValueError(
                f"ActivityCalendar could not convert dates in {label}."
            ) from error
        if normalized.isna().any():
            raise ValueError(f"ActivityCalendar found missing dates in {label}.")
        return normalized

    @staticmethod
    def _normalize_boundary(value, label):
        try:
            parsed = pd.to_datetime(value, errors="raise")
            if not isinstance(parsed, pd.Timestamp):
                parsed = pd.Timestamp(parsed)
            parsed = parsed.tz_localize(None).normalize()
        except (TypeError, ValueError, OverflowError) as error:
            raise ValueError(
                f"ActivityCalendar could not convert {label} to a date."
            ) from error
        if pd.isna(parsed):
            raise ValueError(f"ActivityCalendar {label} cannot be missing.")
        return parsed

    @staticmethod
    def _parse_hex_color(color):
        if not isinstance(color, str) or not color.startswith("#"):
            return None
        value = color[1:]
        if len(value) == 3:
            value = "".join(character * 2 for character in value)
        if len(value) != 6:
            return None
        try:
            return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))
        except ValueError:
            return None

    @classmethod
    def _resolve_color(cls, color):
        if color is None:
            color = "green"
        if not isinstance(color, str):
            raise ValueError(
                "ActivityCalendar color must be 'green', 'red', or a hex color."
            )

        normalized = color.strip()
        preset = cls._COLOR_PRESETS.get(normalized.lower())
        if preset is not None:
            fallback = "#19b96c" if preset == "success_color" else "#dc3545"
            return THEME.get(preset, fallback)
        if cls._parse_hex_color(normalized) is not None:
            return normalized
        raise ValueError(
            "ActivityCalendar color must be 'green', 'red', or a hex color "
            "such as '#f85149'."
        )

    @classmethod
    def _mix_colors(cls, foreground, background, ratio):
        foreground_rgb = cls._parse_hex_color(foreground)
        background_rgb = cls._parse_hex_color(background)
        if foreground_rgb is None or background_rgb is None:
            return foreground
        mixed = tuple(
            round(foreground_channel * ratio + background_channel * (1 - ratio))
            for foreground_channel, background_channel in zip(
                foreground_rgb, background_rgb
            )
        )
        return "#{:02x}{:02x}{:02x}".format(*mixed)

    def _level(self, value):
        if (
            value is None
            or pd.isna(value)
            or float(value) <= 0
            or self._max_value <= 0
        ):
            return 0
        return min(
            self.levels - 1,
            max(1, math.ceil(float(value) / self._max_value * (self.levels - 1))),
        )

    @staticmethod
    def _format_value(value):
        if isinstance(value, Integral):
            return str(int(value))
        if isinstance(value, Real):
            return f"{float(value):g}"
        return str(value)

    def _tooltip(self, day, value):
        date_label = f"{day.strftime('%B')} {day.day}, {day.year}"
        if value is None or pd.isna(value) or float(value) <= 0:
            return f"{date_label}\nNo activity"
        value_label = self._format_value(value)
        if self.unit:
            value_label = f"{value_label} {self.unit}"
        return f"{date_label}\n{value_label}"

    def _styles(self):
        return """
<style>
.mljar-activity-calendar {
    max-width: 100%%;
    color: %(text_color)s;
    font-family: %(font_family)s;
}
.mljar-activity-calendar-title {
    margin: 0 0 12px;
    color: %(text_color)s;
    font-family: %(heading_font_family)s;
    font-size: 16px;
    font-weight: 600;
}
.mljar-activity-calendar-year + .mljar-activity-calendar-year {
    margin-top: 18px;
}
.mljar-activity-calendar-year-label {
    margin: 0 0 6px;
    color: %(text_color)s;
    font-size: 14px;
    font-weight: 600;
}
.mljar-activity-calendar-scroll {
    max-width: 100%%;
    overflow-x: auto;
    padding-bottom: 3px;
}
.mljar-activity-calendar-svg {
    display: block;
    max-width: none;
}
.mljar-activity-calendar-month,
.mljar-activity-calendar-weekday {
    fill: %(muted_text_color)s;
    font-size: 10px;
}
.mljar-activity-calendar-day {
    stroke: %(border_color)s;
    stroke-width: 0.5;
}
.mljar-activity-calendar-legend {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    flex-wrap: wrap;
    gap: 5px;
    margin-top: 8px;
    color: %(muted_text_color)s;
    font-size: 11px;
}
.mljar-activity-calendar-legend-scale {
    display: inline-flex;
    gap: 3px;
}
.mljar-activity-calendar-legend-cell {
    width: %(cell_size)spx;
    height: %(cell_size)spx;
    border: 0.5px solid %(border_color)s;
    border-radius: 2px;
    box-sizing: border-box;
}
.mljar-activity-calendar-unit {
    margin-right: 4px;
}
</style>""" % {
            "font_family": THEME.get("font_family", "Arial, sans-serif"),
            "heading_font_family": THEME.get(
                "heading_font_family", THEME.get("font_family", "Arial, sans-serif")
            ),
            "text_color": THEME.get("text_color", "#0f172a"),
            "muted_text_color": THEME.get("muted_text_color", "#475569"),
            "border_color": THEME.get("border_color", "#d0d7de"),
            "cell_size": self._CELL_SIZE,
        }

    def _year_svg(self, year):
        year_start = pd.Timestamp(year=year, month=1, day=1)
        year_end = pd.Timestamp(year=year, month=12, day=31)
        segment_start = max(self.start_date, year_start)
        segment_end = min(self.end_date, year_end)
        multiple_years = len(self._years()) > 1
        layout_start = year_start if multiple_years else segment_start
        layout_end = year_end if multiple_years else segment_end
        week_anchor = layout_start - pd.Timedelta(days=layout_start.weekday())
        week_count = (
            self._MULTI_YEAR_WEEK_COUNT
            if multiple_years
            else ((layout_end - week_anchor).days // 7) + 1
        )
        step = self._CELL_SIZE + self._CELL_GAP
        left = self._WEEKDAY_LABEL_WIDTH if self.show_weekdays else 0
        top = self._MONTH_LABEL_HEIGHT if self.show_months else 0
        width = left + week_count * step - self._CELL_GAP
        height = top + 7 * step - self._CELL_GAP
        elements = []

        if self.show_months:
            month = segment_start.replace(day=1)
            while month <= segment_end:
                visible_month_day = max(month, segment_start)
                week = (
                    round((month.month - 1) * 52 / 12)
                    if multiple_years
                    else (visible_month_day - week_anchor).days // 7
                )
                x = left + week * step
                elements.append(
                    f'<text class="mljar-activity-calendar-month" x="{x}" y="11">'
                    f"{escape(month.strftime('%b'))}</text>"
                )
                month = month + pd.offsets.MonthBegin(1)

        if self.show_weekdays:
            for row, label in ((0, "Mon"), (2, "Wed"), (4, "Fri"), (6, "Sun")):
                y = top + row * step + self._CELL_SIZE - 1
                elements.append(
                    f'<text class="mljar-activity-calendar-weekday" x="0" y="{y}">'
                    f"{label}</text>"
                )

        for day in pd.date_range(segment_start, segment_end, freq="D"):
            week = (day - week_anchor).days // 7
            row = day.weekday()
            x = left + week * step
            y = top + row * step
            value = self._values.get(day)
            level = self._level(value)
            fill = (
                self._inactive_color
                if level == 0
                else self._active_colors[level - 1]
            )
            tooltip = self._tooltip(day, value)
            escaped_tooltip = escape(tooltip, quote=True)
            elements.append(
                f'<rect class="mljar-activity-calendar-day" '
                f'data-date="{day.date().isoformat()}" data-level="{level}" '
                f'x="{x}" y="{y}" width="{self._CELL_SIZE}" '
                f'height="{self._CELL_SIZE}" rx="2" fill="{escape(fill, quote=True)}" '
                f'aria-label="{escaped_tooltip}"><title>{escape(tooltip)}</title>'
                "</rect>"
            )

        svg = (
            f'<svg class="mljar-activity-calendar-svg" '
            f'width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
            f'role="img" aria-label="Activity calendar for {year}" '
            f'xmlns="http://www.w3.org/2000/svg">{"".join(elements)}</svg>'
        )
        year_label = (
            f'<div class="mljar-activity-calendar-year-label">{year}</div>'
            if len(self._years()) > 1
            else ""
        )
        return (
            '<div class="mljar-activity-calendar-year">'
            f"{year_label}"
            '<div class="mljar-activity-calendar-scroll">'
            f"{svg}</div></div>"
        )

    def _years(self):
        return list(range(self.start_date.year, self.end_date.year + 1))

    def _legend_html(self):
        if not self.show_legend:
            return ""
        colors = [self._inactive_color, *self._active_colors]
        cells = "".join(
            '<span class="mljar-activity-calendar-legend-cell" '
            f'style="background:{escape(color, quote=True)}"></span>'
            for color in colors
        )
        unit = (
            '<span class="mljar-activity-calendar-unit">'
            f"{escape(str(self.unit))}</span>"
            if self.unit
            else ""
        )
        return (
            '<div class="mljar-activity-calendar-legend">'
            f"{unit}<span>Less</span>"
            '<span class="mljar-activity-calendar-legend-scale">'
            f"{cells}</span><span>More</span></div>"
        )

    def display(self):
        display(self)

    def _repr_html_(self):
        title = (
            '<div class="mljar-activity-calendar-title">'
            f"{escape(str(self.title))}</div>"
            if self.title
            else ""
        )
        calendars = "".join(self._year_svg(year) for year in self._years())
        return (
            f"{self._styles()}"
            '<div class="mljar-activity-calendar">'
            f"{title}{calendars}{self._legend_html()}"
            "</div>"
        )
