import math

import pandas as pd
import pytest

import mercury.sankey as sankey_module
from mercury.sankey import (
    Sankey,
    _assign_depths,
    _build_graph,
    _calculate_link_layout,
    _calculate_node_layout,
    _normalize_data,
    _order_nodes,
    _topological_sort,
)
from mercury.theme import THEME


def simple_links():
    return [("A", "B", 100), ("A", "C", 50)]


def test_dataframe_input_is_normalized():
    data = pd.DataFrame(
        {"source": ["A", "A"], "target": ["B", "C"], "value": [10, 5.5]}
    )

    assert _normalize_data(data) == [
        {"source": "A", "target": "B", "value": 10.0},
        {"source": "A", "target": "C", "value": 5.5},
    ]


def test_custom_dataframe_column_names_are_supported():
    data = pd.DataFrame({"from": ["A"], "to": ["B"], "count": [3]})

    widget = Sankey(data, source="from", target="to", value="count")

    assert widget.links == [{"source": "A", "target": "B", "value": 3.0}]


def test_tuple_and_dictionary_rows_are_supported():
    tuples = Sankey([("A", "B", 2), ("B", "C", 1)])
    dictionaries = Sankey(
        [
            {"from": "A", "to": "B", "amount": 2},
            {"from": "B", "to": "C", "amount": 1},
        ],
        source="from",
        target="to",
        value="amount",
    )

    assert tuples.links == dictionaries.links


def test_duplicate_links_are_aggregated_in_first_seen_order():
    links = _normalize_data(
        [("A", "B", 10), ("C", "D", 2), ("A", "B", 15.5)]
    )

    assert links == [
        {"source": "A", "target": "B", "value": 25.5},
        {"source": "C", "target": "D", "value": 2.0},
    ]


def test_zero_value_links_are_removed():
    links = _normalize_data([("A", "B", 0), ("A", "C", 4)])

    assert links == [{"source": "A", "target": "C", "value": 4.0}]


def test_node_names_are_trimmed_and_first_seen_order_is_deterministic():
    widget = Sankey([(" B ", "D", 1), ("A", "C", 1), ("B", "C", 1)])

    assert widget.graph["nodes"] == ["B", "D", "A", "C"]
    assert widget.columns == Sankey(
        [(" B ", "D", 1), ("A", "C", 1), ("B", "C", 1)]
    ).columns


@pytest.mark.parametrize(
    ("missing", "message"),
    [
        ("source", "source column 'source' was not found"),
        ("target", "target column 'target' was not found"),
        ("value", "value column 'value' was not found"),
    ],
)
def test_missing_dataframe_columns_raise_clear_errors(missing, message):
    columns = {
        "source": ["A"],
        "target": ["B"],
        "value": [1],
    }
    columns.pop(missing)

    with pytest.raises(ValueError, match=message):
        Sankey(pd.DataFrame(columns))


@pytest.mark.parametrize("value", ["1", True, pd.Series([True]).iloc[0], None])
def test_non_numeric_values_are_rejected(value):
    with pytest.raises(ValueError, match="values must be numeric"):
        Sankey([("A", "B", value)])


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_nan_and_infinite_values_are_rejected(value):
    with pytest.raises(ValueError, match="must be finite"):
        Sankey([("A", "B", value)])


def test_negative_values_are_rejected():
    with pytest.raises(ValueError, match="cannot be negative"):
        Sankey([("A", "B", -1)])


@pytest.mark.parametrize("source,target", [("", "B"), (None, "B"), ("A", " ")])
def test_empty_node_names_are_rejected(source, target):
    with pytest.raises(ValueError, match="values cannot be empty"):
        Sankey([(source, target, 1)])


def test_self_links_are_rejected():
    with pytest.raises(ValueError, match="self-links are not supported"):
        Sankey([("A", "A", 1)])


def test_cycles_include_the_detected_path():
    with pytest.raises(ValueError) as error:
        Sankey([("A", "B", 1), ("B", "C", 1), ("C", "A", 1)])

    message = str(error.value)
    assert "require an acyclic graph" in message
    assert "A -> B -> C -> A" in message


@pytest.mark.parametrize("data", [[], [("A", "B", 0)]])
def test_empty_positive_flow_data_is_rejected(data):
    with pytest.raises(ValueError, match="at least one positive flow"):
        Sankey(data)


def test_malformed_rows_and_input_types_are_rejected():
    with pytest.raises(ValueError, match="three-item tuple"):
        Sankey([("A", "B")])
    with pytest.raises(ValueError, match="missing required key"):
        Sankey([{"source": "A", "target": "B"}])
    with pytest.raises(TypeError, match="pandas DataFrame"):
        Sankey("A -> B")


def test_simple_graph_assigns_two_columns():
    widget = Sankey([("A", "B", 1)])

    assert widget.depths == {"A": 0, "B": 1}
    assert widget.columns == [["A"], ["B"]]


def test_one_to_many_and_many_to_one_layouts():
    branching = Sankey([("A", "B", 2), ("A", "C", 1)])
    merging = Sankey([("A", "C", 2), ("B", "C", 1)])

    assert branching.columns[0] == ["A"]
    assert set(branching.columns[-1]) == {"B", "C"}
    assert set(merging.columns[0]) == {"A", "B"}
    assert merging.columns[-1] == ["C"]


def test_three_stage_funnel_and_terminal_alignment():
    widget = Sankey(
        [
            ("Visitors", "Signup", 800),
            ("Visitors", "Left", 200),
            ("Signup", "Paid", 120),
            ("Signup", "Free", 680),
        ]
    )

    assert widget.depths["Visitors"] == 0
    assert widget.depths["Signup"] == 1
    assert widget.depths["Left"] == 2
    assert widget.depths["Paid"] == 2
    assert widget.depths["Free"] == 2


def test_disconnected_flows_and_multiple_roots_are_supported():
    widget = Sankey(
        [("A", "B", 2), ("X", "Y", 3), ("Y", "Z", 3), ("M", "Z", 1)]
    )

    assert {"A", "X", "M"}.issubset(set(widget.columns[0]))
    assert {"B", "Z"}.issubset(set(widget.columns[-1]))


def test_barycentric_ordering_is_deterministic():
    links = _normalize_data(
        [("A", "D", 1), ("A", "C", 3), ("B", "C", 1), ("B", "D", 3)]
    )
    graph = _build_graph(links)
    topological = _topological_sort(graph)
    depths = _assign_depths(graph, topological)

    first = _order_nodes(graph, depths)
    second = _order_nodes(graph, depths)

    assert first == second
    assert first[0] == ["A", "B"]
    assert first[1] == ["C", "D"]


def test_node_and_link_thickness_share_one_scale():
    links = _normalize_data(simple_links())
    graph = _build_graph(links)
    topological = _topological_sort(graph)
    depths = _assign_depths(graph, topological)
    columns = _order_nodes(graph, depths)
    nodes, scale = _calculate_node_layout(graph, columns, 400, 16, 16, 600)
    link_layout = _calculate_link_layout(graph, nodes, scale)

    assert nodes["A"]["height"] == pytest.approx(150 * scale)
    for link in link_layout:
        source_thickness = link["source_bottom"] - link["source_top"]
        target_thickness = link["target_bottom"] - link["target_top"]
        assert source_thickness == pytest.approx(link["value"] * scale)
        assert target_thickness == pytest.approx(link["value"] * scale)


def test_svg_contains_nodes_filled_ribbons_labels_and_tooltips():
    html = Sankey([("Visitors", "Signup", 800)])._repr_html_()

    assert '<svg class="mljar-sankey-svg"' in html
    assert '<path class="mljar-sankey-link"' in html
    assert " C " in html
    assert " Z\"" in html
    path_tag = html.split('<path class="mljar-sankey-link"', 1)[1].split(">", 1)[0]
    assert "stroke-width" not in path_tag
    assert '<rect class="mljar-sankey-node"' in html
    assert ">Visitors</text>" in html
    assert ">Signup</text>" in html
    assert "Visitors → Signup: 800" in html
    assert "Signup — 800" in html


def test_custom_color_list_cycles_and_colors_links_by_source():
    widget = Sankey(simple_links(), colors=["#123456", "#abcdef"])
    html = widget._repr_html_()

    assert widget.node_colors == {"A": "#123456", "B": "#abcdef", "C": "#123456"}
    assert 'class="mljar-sankey-link"' in html
    assert 'fill="#123456"' in html


def test_custom_color_dictionary_uses_defaults_for_unmapped_nodes():
    widget = Sankey(simple_links(), colors={"A": "#abc"})

    assert widget.node_colors["A"] == "#aabbcc"
    assert widget.node_colors["B"] == THEME["success_color"]


def test_link_opacity_and_values_are_rendered():
    html = Sankey(
        [("Visitors", "Signup", 1000)],
        link_opacity=0.2,
        show_values=True,
        value_format=",",
    )._repr_html_()

    assert 'opacity="0.2"' in html
    assert "Visitors · 1,000" in html
    assert "Signup · 1,000" in html


def test_user_labels_are_html_escaped_everywhere():
    label = '<script>alert("x")</script>'
    html = Sankey([(label, "Safe", 1)])._repr_html_()

    assert "<script>" not in html
    assert "&lt;script&gt;alert" in html
    assert "&quot;x&quot;" in html


def test_accessibility_and_responsive_wrapper_are_rendered():
    html = Sankey(simple_links())._repr_html_()

    assert 'role="img" aria-label="Sankey diagram with 3 nodes and 2 flows"' in html
    assert "Ribbon width represents flow value." in html
    assert "overflow-x: auto;" in html
    assert "width: 100%;" in html
    assert "min-width: 600px;" in html


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"height": 100}, "height"),
        ({"node_width": 0}, "node_width"),
        ({"node_padding": -1}, "node_padding"),
        ({"link_opacity": -0.1}, "link_opacity"),
        ({"link_opacity": 1.1}, "link_opacity"),
        ({"value_format": 2}, "value_format"),
        ({"value_format": "invalid"}, "value_format"),
        ({"colors": []}, "colors cannot be an empty"),
        ({"colors": ["red"]}, "hex values"),
    ],
)
def test_invalid_configuration_is_rejected(kwargs, message):
    with pytest.raises(ValueError, match=message):
        Sankey(simple_links(), **kwargs)


def test_display_method_displays_the_sankey(monkeypatch):
    displayed = []
    monkeypatch.setattr(
        sankey_module, "display", lambda widget: displayed.append(widget)
    )
    widget = Sankey(simple_links())

    widget.display()

    assert displayed == [widget]


def test_sankey_is_exported_from_mercury():
    import mercury as mr

    assert mr.Sankey is Sankey
