import math

import pandas as pd
import pytest

import mercury as mr
from mercury.funnel import (
    Funnel,
    _calculate_layout,
    _calculate_percentages,
    _format_percentage,
    _format_value,
    _normalize_data,
)


def stages():
    return [("Visitors", 1000), ("Signup", 500), ("Trial", 100)]


def test_funnel_is_exported_from_public_api():
    assert mr.Funnel is Funnel


def test_dataframe_input_and_custom_columns_are_normalized():
    data = pd.DataFrame(
        {"step": ["Visitors", "Paid"], "users": [1000, 42.5]}
    )

    widget = Funnel(data, stage="step", value="users")

    assert widget.stages == [
        {"stage": "Visitors", "value": 1000.0},
        {"stage": "Paid", "value": 42.5},
    ]


def test_tuple_dictionary_and_row_dictionary_inputs_preserve_order():
    expected = [
        {"stage": "Visitors", "value": 1000.0},
        {"stage": "Paid", "value": 50.0},
    ]

    assert _normalize_data([("Visitors", 1000), ("Paid", 50)]) == expected
    assert _normalize_data({"Visitors": 1000, "Paid": 50}) == expected
    assert _normalize_data(
        [
            {"step": "Visitors", "users": 1000},
            {"step": "Paid", "users": 50},
        ],
        stage="step",
        value="users",
    ) == expected


def test_zero_float_and_single_stage_values_are_supported():
    zero = Funnel([("Visitors", 1000), ("Paid", 0)])
    single = Funnel([("Revenue", 12500.5)])

    assert zero.stages[-1]["value"] == 0
    assert zero.layout[-1]["top_width"] == 0
    assert single.layout[0]["top_width"] == single.layout[0]["bottom_width"]


@pytest.mark.parametrize("data", [[], {}, pd.DataFrame(columns=["stage", "value"])])
def test_empty_data_is_rejected(data):
    with pytest.raises(ValueError, match="at least one stage"):
        Funnel(data)


@pytest.mark.parametrize(
    ("missing", "message"),
    [
        ("stage", "stage column 'stage' was not found"),
        ("value", "value column 'value' was not found"),
    ],
)
def test_missing_dataframe_columns_are_rejected(missing, message):
    columns = {"stage": ["A"], "value": [1]}
    columns.pop(missing)

    with pytest.raises(ValueError, match=message):
        Funnel(pd.DataFrame(columns))


@pytest.mark.parametrize("stage", ["", "  ", None, float("nan")])
def test_empty_stage_names_are_rejected(stage):
    with pytest.raises(ValueError, match="stage names cannot be empty"):
        Funnel([(stage, 1)])


@pytest.mark.parametrize("value", ["1", True, None])
def test_non_numeric_values_are_rejected(value):
    with pytest.raises(ValueError, match="values must be numeric"):
        Funnel([("A", value)])


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_non_finite_values_are_rejected(value):
    with pytest.raises(ValueError, match="values must be finite"):
        Funnel([("A", value)])


def test_negative_values_are_rejected():
    with pytest.raises(ValueError, match="cannot be negative"):
        Funnel([("A", -1)])


def test_malformed_rows_and_input_types_are_rejected():
    with pytest.raises(ValueError, match="two-item tuple"):
        Funnel([("A", 1, "extra")])
    with pytest.raises(ValueError, match="missing required key"):
        Funnel([{"stage": "A"}])
    with pytest.raises(TypeError, match="pandas DataFrame"):
        Funnel("A: 1")


def test_previous_stage_percentages():
    normalized = _normalize_data(stages())

    assert _calculate_percentages(normalized, "previous") == [100, 50, 20]


def test_first_stage_percentages():
    normalized = _normalize_data(stages())

    assert _calculate_percentages(normalized, "first") == [100, 50, 10]


@pytest.mark.parametrize("mode", ["previous", "first"])
def test_zero_percentage_denominators_are_undefined(mode):
    normalized = _normalize_data([("Initial", 0), ("Next", 10), ("Last", 5)])

    percentages = _calculate_percentages(normalized, mode)

    assert percentages[0] == 100
    assert percentages[1] is None
    if mode == "previous":
        assert percentages[2] == 50
    else:
        assert percentages[2] is None
    assert _format_percentage(None) == "—"


def test_invalid_percentage_option_is_rejected():
    with pytest.raises(ValueError, match="'previous' or 'first'"):
        Funnel(stages(), percentage="total")


def test_increasing_stage_percentage_is_not_clamped():
    widget = Funnel([("Invited", 100), ("Registered", 120), ("Paid", 20)])

    assert widget.percentages[1] == 120
    assert "120%" in widget._repr_html_()


def test_value_and_percentage_formatting():
    assert _format_value(10000, ",") == "10,000"
    assert _format_value(12500.5, ",") == "12,500.5"
    assert _format_percentage(28.3333) == "28.3%"
    assert _format_percentage(50) == "50%"


def test_invalid_value_format_is_rejected():
    with pytest.raises(ValueError, match="value_format"):
        Funnel(stages(), value_format="invalid-format")


def test_largest_and_smaller_stage_widths_are_proportional():
    normalized = _normalize_data([("Largest", 100), ("Half", 50)])
    layout, _ = _calculate_layout(normalized)

    assert layout[0]["top_width"] == pytest.approx(440)
    assert layout[1]["top_width"] == pytest.approx(220)


def test_stages_are_centered_and_last_stage_is_rectangular():
    normalized = _normalize_data(stages())
    layout, _ = _calculate_layout(normalized)

    for geometry in layout:
        assert (geometry["x1"] + geometry["x2"]) / 2 == pytest.approx(244)
        assert (geometry["x3"] + geometry["x4"]) / 2 == pytest.approx(244)
    assert layout[-1]["top_width"] == layout[-1]["bottom_width"]


def test_positive_minimum_width_and_true_zero_width():
    normalized = _normalize_data([("Large", 1_000_000), ("Tiny", 1), ("Zero", 0)])
    layout, _ = _calculate_layout(normalized)

    assert layout[1]["top_width"] == 6
    assert layout[2]["top_width"] == 0


def test_explicit_height_is_distributed_and_too_small_height_is_rejected():
    widget = Funnel(stages(), height=400)

    assert widget.height == 400
    assert all(math.isclose(item["y2"] - item["y1"], 114.6666666667) for item in widget.layout)
    with pytest.raises(ValueError, match="height must be at least"):
        Funnel(stages(), height=100)


def test_svg_contains_shapes_labels_values_percentages_and_tooltips():
    html = Funnel(stages())._repr_html_()

    assert '<svg class="mljar-funnel-svg"' in html
    assert 'role="img" aria-label="Funnel chart with 3 stages"' in html
    assert html.count('<polygon class="mljar-funnel-stage"') == 3
    assert ">Visitors</text>" in html
    assert "1,000 · 100%" in html
    assert "Signup: 500 — 50% of previous stage" in html


def test_values_and_percentages_can_be_hidden_independently():
    without_values = Funnel(stages(), show_values=False)._repr_html_()
    without_percentages = Funnel(stages(), show_percentage=False)._repr_html_()
    minimal = Funnel(
        stages(), show_values=False, show_percentage=False
    )._repr_html_()

    assert ">100%</text>" in without_values
    assert ">1,000 ·" not in without_values
    assert " · 100%</text>" not in without_percentages
    assert 'class="mljar-funnel-meta-label"' not in minimal


def test_custom_color_list_cycles_and_mapping_uses_defaults():
    cycled = Funnel(stages(), colors=["#123", "#abcdef"])
    mapped = Funnel(stages(), colors={"Signup": "#00ff00"})

    assert cycled.colors == ["#112233", "#abcdef", "#112233"]
    assert mapped.colors[1] == "#00ff00"
    assert mapped.colors[0].startswith("#")


@pytest.mark.parametrize("colors", [[], ["red"], {"A": "blue"}, "#ffffff"])
def test_invalid_colors_are_rejected(colors):
    with pytest.raises(ValueError, match="Funnel colors"):
        Funnel(stages(), colors=colors)


def test_stage_names_are_html_escaped_everywhere():
    malicious = '<script>alert("x")</script>'
    html = Funnel([(malicious, 1)])._repr_html_()

    assert malicious not in html
    assert "&lt;script&gt;alert" in html
    assert "&quot;x&quot;" in html


def test_svg_is_responsive_and_uses_theme_text_styles():
    html = Funnel(stages())._repr_html_()

    assert "viewBox=" in html
    assert "width: 100%;" in html
    assert "overflow-x: auto" in html
    assert "mljar-funnel-stage-label" in html
