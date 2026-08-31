import pandas as pd
import pytest

import mercury.activity_calendar as activity_calendar_module
from mercury.activity_calendar import ActivityCalendar
from mercury.theme import THEME


def calendar(data, **kwargs):
    return ActivityCalendar(data, date="date", value="value", **kwargs)


def test_basic_dataframe_renders_svg_dates_and_cells():
    widget = calendar(
        pd.DataFrame(
            {
                "date": ["2026-08-20", "2026-08-21"],
                "value": [0.5, 2.1],
            }
        )
    )

    html = widget._repr_html_()

    assert '<svg class="mljar-activity-calendar-svg"' in html
    assert html.count('<rect class="mljar-activity-calendar-day"') == 2
    assert 'data-date="2026-08-20"' in html
    assert 'data-date="2026-08-21"' in html
    assert "August 20, 2026\n0.5" in html


def test_accepts_pandas_timestamps_and_normalizes_times_to_days():
    widget = calendar(
        pd.DataFrame(
            {
                "date": [
                    pd.Timestamp("2026-08-20 09:30"),
                    pd.Timestamp("2026-08-21 18:45"),
                ],
                "value": [1, 2],
            }
        )
    )

    assert widget.start_date == pd.Timestamp("2026-08-20")
    assert widget.end_date == pd.Timestamp("2026-08-21")


def test_zero_value_is_inactive():
    html = calendar(
        pd.DataFrame({"date": ["2026-08-20"], "value": [0]})
    )._repr_html_()

    assert 'data-level="0"' in html
    assert "August 20, 2026\nNo activity" in html


def test_missing_calendar_days_are_rendered_as_inactive():
    html = calendar(
        pd.DataFrame(
            {
                "date": ["2026-01-01", "2026-01-05"],
                "value": [10, 20],
            }
        )
    )._repr_html_()

    assert html.count('<rect class="mljar-activity-calendar-day"') == 5
    assert 'data-date="2026-01-03" data-level="0"' in html
    assert "January 3, 2026\nNo activity" in html


def test_custom_start_date_extends_the_calendar():
    widget = calendar(
        pd.DataFrame({"date": ["2026-01-03"], "value": [2]}),
        start_date="2026-01-01",
    )
    html = widget._repr_html_()

    assert widget.start_date == pd.Timestamp("2026-01-01")
    assert 'data-date="2026-01-01" data-level="0"' in html
    assert html.count('<rect class="mljar-activity-calendar-day"') == 3


def test_custom_end_date_extends_the_calendar():
    widget = calendar(
        pd.DataFrame({"date": ["2026-01-03"], "value": [2]}),
        end_date=pd.Timestamp("2026-01-05 14:00"),
    )
    html = widget._repr_html_()

    assert widget.end_date == pd.Timestamp("2026-01-05")
    assert 'data-date="2026-01-05" data-level="0"' in html
    assert html.count('<rect class="mljar-activity-calendar-day"') == 3


def test_custom_color_is_the_strongest_level():
    html = calendar(
        pd.DataFrame({"date": ["2026-01-01"], "value": [10]}),
        color="#f85149",
    )._repr_html_()

    assert 'data-level="4"' in html
    assert 'fill="#f85149"' in html


def test_default_strongest_color_uses_mercury_success_color():
    widget = calendar(
        pd.DataFrame({"date": ["2026-01-01"], "value": [10]})
    )
    html = widget._repr_html_()

    assert f'fill="{THEME["success_color"]}"' in html
    assert len(set(widget._active_colors)) == widget.levels - 1


@pytest.mark.parametrize(
    ("color", "theme_color"),
    [
        ("green", "success_color"),
        ("GREEN", "success_color"),
        ("red", "danger_color"),
        ("RED", "danger_color"),
    ],
)
def test_named_color_presets_are_case_insensitive(color, theme_color):
    widget = calendar(
        pd.DataFrame({"date": ["2026-01-01"], "value": [10]}), color=color
    )

    assert widget._strongest_color == THEME[theme_color]
    assert widget._active_colors[-1] == THEME[theme_color]


def test_short_custom_hex_color_is_supported_and_expanded_for_intensity():
    widget = calendar(
        pd.DataFrame({"date": ["2026-01-01"], "value": [10]}), color="#abc"
    )

    assert widget._active_colors[-1] == "#aabbcc"


@pytest.mark.parametrize("color", ["blue", "#12", "#gggggg", 42])
def test_invalid_color_is_rejected(color):
    data = pd.DataFrame({"date": ["2026-01-01"], "value": [1]})

    with pytest.raises(ValueError, match="color must be 'green', 'red'"):
        calendar(data, color=color)


def test_linear_intensity_uses_all_configured_levels():
    html = calendar(
        pd.DataFrame(
            {
                "date": pd.date_range("2026-01-01", periods=5),
                "value": [0, 1, 2, 3, 4],
            }
        )
    )._repr_html_()

    for expected_level in range(5):
        assert f'data-level="{expected_level}"' in html


def test_legend_contains_one_cell_per_level():
    html = calendar(
        pd.DataFrame({"date": ["2026-01-01"], "value": [1]}), levels=7
    )._repr_html_()

    assert html.count('<span class="mljar-activity-calendar-legend-cell"') == 7


def test_title_and_unit_are_rendered_including_tooltip():
    html = calendar(
        pd.DataFrame({"date": ["2026-08-23"], "value": [4.8]}),
        title="GitHub outages",
        unit="hours",
    )._repr_html_()

    assert '<div class="mljar-activity-calendar-title">GitHub outages</div>' in html
    assert "August 23, 2026\n4.8 hours" in html
    assert '<span class="mljar-activity-calendar-unit">hours</span>' in html


def test_multiple_years_render_separate_calendars_with_one_scale():
    html = calendar(
        pd.DataFrame(
            {
                "date": ["2025-12-31", "2026-01-01"],
                "value": [1, 4],
            }
        )
    )._repr_html_()

    assert html.count('<svg class="mljar-activity-calendar-svg"') == 2
    assert '<div class="mljar-activity-calendar-year-label">2025</div>' in html
    assert '<div class="mljar-activity-calendar-year-label">2026</div>' in html
    assert 'data-date="2025-12-31" data-level="1"' in html
    assert 'data-date="2026-01-01" data-level="4"' in html


def test_hidden_legend_is_not_rendered():
    html = calendar(
        pd.DataFrame({"date": ["2026-01-01"], "value": [1]}),
        show_legend=False,
    )._repr_html_()

    assert '<div class="mljar-activity-calendar-legend">' not in html
    assert "<span>Less</span>" not in html


def test_hidden_weekdays_are_not_rendered_or_reserved():
    widget = calendar(
        pd.DataFrame({"date": ["2026-01-01"], "value": [1]}),
        show_weekdays=False,
    )
    html = widget._repr_html_()

    assert '<text class="mljar-activity-calendar-weekday"' not in html
    assert 'data-date="2026-01-01" data-level="4" x="0"' in html


def test_hidden_months_are_not_rendered_or_reserved():
    widget = calendar(
        pd.DataFrame({"date": ["2026-01-01"], "value": [1]}),
        show_months=False,
    )
    html = widget._repr_html_()

    assert '<text class="mljar-activity-calendar-month"' not in html
    assert 'data-date="2026-01-01" data-level="4" x="32" y="42"' in html


def test_calendar_uses_a_fixed_width_inside_responsive_scroll_container():
    html = calendar(
        pd.DataFrame({"date": ["2026-01-01"], "value": [1]})
    )._repr_html_()

    assert "max-width: 100%;" in html
    assert "overflow-x: auto;" in html
    assert "max-width: none;" in html


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"date": "missing"}, "date column 'missing' was not found"),
        ({"value": "missing"}, "value column 'missing' was not found"),
    ],
)
def test_missing_columns_raise_clear_errors(kwargs, message):
    data = pd.DataFrame({"date": ["2026-01-01"], "value": [1]})

    with pytest.raises(ValueError, match=message):
        ActivityCalendar(data, **kwargs)


def test_non_numeric_values_are_rejected():
    data = pd.DataFrame({"date": ["2026-01-01"], "value": ["high"]})

    with pytest.raises(ValueError, match="must contain numeric values"):
        calendar(data)


def test_invalid_dates_are_rejected():
    data = pd.DataFrame({"date": ["not-a-date"], "value": [1]})

    with pytest.raises(ValueError, match="could not convert dates"):
        calendar(data)


def test_duplicate_normalized_dates_are_rejected_without_aggregation():
    data = pd.DataFrame(
        {
            "date": ["2026-01-01 09:00", "2026-01-01 18:00"],
            "value": [1, 2],
        }
    )

    with pytest.raises(ValueError, match="Aggregate duplicate dates"):
        calendar(data)


def test_empty_dataframe_is_rejected():
    with pytest.raises(ValueError, match="non-empty DataFrame"):
        calendar(pd.DataFrame(columns=["date", "value"]))


@pytest.mark.parametrize("levels", [1, 0, -2, 2.5, True])
def test_invalid_levels_are_rejected(levels):
    data = pd.DataFrame({"date": ["2026-01-01"], "value": [1]})

    with pytest.raises(ValueError, match="levels must be an integer"):
        calendar(data, levels=levels)


def test_start_date_after_end_date_is_rejected():
    data = pd.DataFrame({"date": ["2026-01-01"], "value": [1]})

    with pytest.raises(ValueError, match="start_date must be before or equal"):
        calendar(data, start_date="2026-02-01", end_date="2026-01-01")


def test_non_dataframe_is_rejected():
    with pytest.raises(TypeError, match="pandas DataFrame"):
        ActivityCalendar([], date="date", value="value")


def test_tooltip_and_aria_label_contain_the_same_information():
    html = calendar(
        pd.DataFrame({"date": ["2026-08-23"], "value": [4.8]}), unit="hours"
    )._repr_html_()

    label = "August 23, 2026\n4.8 hours"
    assert f'aria-label="{label}"' in html
    assert f"<title>{label}</title>" in html


def test_user_text_is_html_escaped():
    html = calendar(
        pd.DataFrame({"date": ["2026-01-01"], "value": [1]}),
        title="<script>alert(1)</script>",
        unit='hours"<',
    )._repr_html_()

    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "hours&quot;&lt;" in html


def test_display_method_displays_the_calendar(monkeypatch):
    displayed = []
    monkeypatch.setattr(
        activity_calendar_module, "display", lambda widget: displayed.append(widget)
    )
    widget = calendar(pd.DataFrame({"date": ["2026-01-01"], "value": [1]}))

    widget.display()

    assert displayed == [widget]


def test_activity_calendar_is_exported_from_mercury():
    import mercury as mr

    assert mr.ActivityCalendar is ActivityCalendar
