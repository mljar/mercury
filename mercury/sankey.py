import math
from html import escape
from numbers import Real

import pandas as pd
from IPython.display import display

from .theme import THEME


def _normalize_label(raw, field):
    if not pd.api.types.is_scalar(raw) or pd.isna(raw):
        raise ValueError(f"Sankey {field} values cannot be empty.")
    label = str(raw).strip()
    if not label:
        raise ValueError(f"Sankey {field} values cannot be empty.")
    return label


def _normalize_value(raw):
    if pd.api.types.is_bool(raw) or isinstance(raw, (str, bytes)):
        raise ValueError("Sankey values must be numeric.")
    try:
        normalized = float(raw)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("Sankey values must be numeric.") from error
    if not math.isfinite(normalized):
        raise ValueError(
            "Sankey values must be finite; NaN and infinity are unsupported."
        )
    if normalized < 0:
        raise ValueError("Sankey values cannot be negative.")
    return normalized


def _input_rows(data, source, target, value):
    if isinstance(data, pd.DataFrame):
        for column, role in ((source, "source"), (target, "target"), (value, "value")):
            if column not in data.columns:
                raise ValueError(f"Sankey {role} column '{column}' was not found.")
        return data[[source, target, value]].itertuples(index=False, name=None)

    if not isinstance(data, (list, tuple)):
        raise TypeError(
            "Sankey data must be a pandas DataFrame or a list of tuples or "
            "dictionaries."
        )

    rows = []
    for index, row in enumerate(data):
        if isinstance(row, dict):
            missing = [key for key in (source, target, value) if key not in row]
            if missing:
                raise ValueError(
                    f"Sankey row {index} is missing required key '{missing[0]}'."
                )
            rows.append((row[source], row[target], row[value]))
        elif isinstance(row, (list, tuple)) and len(row) == 3:
            rows.append(tuple(row))
        else:
            raise ValueError(
                f"Sankey row {index} must be a three-item tuple or dictionary."
            )
    return rows


def _normalize_data(data, source="source", target="target", value="value"):
    aggregated = {}
    for raw_source, raw_target, raw_value in _input_rows(
        data, source, target, value
    ):
        source_label = _normalize_label(raw_source, "source")
        target_label = _normalize_label(raw_target, "target")
        flow_value = _normalize_value(raw_value)
        if flow_value == 0:
            continue
        if source_label == target_label:
            raise ValueError(
                "Sankey self-links are not supported: "
                f"{source_label} -> {target_label}."
            )
        key = (source_label, target_label)
        aggregated[key] = aggregated.get(key, 0.0) + flow_value
        if not math.isfinite(aggregated[key]):
            raise ValueError("Sankey aggregated values must remain finite.")

    if not aggregated:
        raise ValueError("Sankey requires at least one positive flow.")

    return [
        {"source": source_label, "target": target_label, "value": flow_value}
        for (source_label, target_label), flow_value in aggregated.items()
    ]


def _build_graph(links):
    nodes = []
    seen = set()
    for link in links:
        for node in (link["source"], link["target"]):
            if node not in seen:
                seen.add(node)
                nodes.append(node)

    incoming = {node: [] for node in nodes}
    outgoing = {node: [] for node in nodes}
    for link in links:
        outgoing[link["source"]].append(link)
        incoming[link["target"]].append(link)

    return {
        "nodes": nodes,
        "links": links,
        "incoming": incoming,
        "outgoing": outgoing,
        "order": {node: index for index, node in enumerate(nodes)},
    }


def _find_cycle(graph):
    state = {node: 0 for node in graph["nodes"]}
    stack = []
    stack_index = {}

    def visit(node):
        state[node] = 1
        stack_index[node] = len(stack)
        stack.append(node)
        for link in graph["outgoing"][node]:
            target = link["target"]
            if state[target] == 0:
                cycle = visit(target)
                if cycle:
                    return cycle
            elif state[target] == 1:
                return stack[stack_index[target] :] + [target]
        stack.pop()
        stack_index.pop(node, None)
        state[node] = 2
        return None

    for node in graph["nodes"]:
        if state[node] == 0:
            cycle = visit(node)
            if cycle:
                return cycle
    return None


def _topological_sort(graph):
    cycle = _find_cycle(graph)
    if cycle:
        path = " -> ".join(cycle)
        raise ValueError(
            "Sankey diagrams currently require an acyclic graph.\n"
            f"Cycle detected involving: {path}"
        )

    indegree = {
        node: len(graph["incoming"][node])
        for node in graph["nodes"]
    }
    ready = [node for node in graph["nodes"] if indegree[node] == 0]
    ordered = []
    while ready:
        ready.sort(key=graph["order"].get)
        node = ready.pop(0)
        ordered.append(node)
        for link in graph["outgoing"][node]:
            target = link["target"]
            indegree[target] -= 1
            if indegree[target] == 0:
                ready.append(target)
    return ordered


def _assign_depths(graph, topological_order):
    depths = {node: 0 for node in graph["nodes"]}
    for node in topological_order:
        for link in graph["outgoing"][node]:
            target = link["target"]
            depths[target] = max(depths[target], depths[node] + 1)

    final_depth = max(depths.values())
    for node in graph["nodes"]:
        if not graph["outgoing"][node]:
            depths[node] = final_depth
    return depths


def _expand_links_for_layout(graph, depths):
    """Split links that skip columns into adjacent layout-only segments."""
    routing_nodes = []
    layout_links = []
    for link_index, link in enumerate(graph["links"]):
        source = link["source"]
        target = link["target"]
        previous = source
        for depth in range(depths[source] + 1, depths[target]):
            routing_node = ("__mercury_sankey_route__", link_index, depth)
            routing_nodes.append(routing_node)
            layout_links.append(
                {
                    "source": previous,
                    "target": routing_node,
                    "value": link["value"],
                    "original_source": source,
                    "original_target": target,
                }
            )
            previous = routing_node
        layout_links.append(
            {
                "source": previous,
                "target": target,
                "value": link["value"],
                "original_source": source,
                "original_target": target,
            }
        )

    layout_graph = _build_graph(layout_links)
    layout_graph["nodes"] = graph["nodes"] + routing_nodes
    layout_graph["order"] = {
        node: index for index, node in enumerate(layout_graph["nodes"])
    }
    layout_depths = dict(depths)
    for routing_node in routing_nodes:
        layout_depths[routing_node] = routing_node[2]
    return layout_graph, layout_depths, set(routing_nodes)


def _order_nodes(graph, depths, passes=4):
    max_depth = max(depths.values())
    columns = [
        [node for node in graph["nodes"] if depths[node] == depth]
        for depth in range(max_depth + 1)
    ]
    first_seen = graph["order"]

    def positions():
        return {
            node: (index + 0.5) / len(column)
            for column in columns
            for index, node in enumerate(column)
        }

    def reorder(column_index, neighbors_for):
        rank = positions()
        current = {node: index for index, node in enumerate(columns[column_index])}

        def key(node):
            neighbors = neighbors_for(node)
            if not neighbors:
                return current[node], first_seen[node]
            total_weight = sum(weight for _, weight in neighbors)
            barycenter = sum(rank[other] * weight for other, weight in neighbors)
            barycenter /= total_weight
            return barycenter, first_seen[node]

        columns[column_index].sort(key=key)

    for _ in range(passes):
        for depth in range(1, max_depth + 1):
            reorder(
                depth,
                lambda node: [
                    (link["source"], link["value"])
                    for link in graph["incoming"][node]
                ],
            )
        for depth in range(max_depth - 1, -1, -1):
            reorder(
                depth,
                lambda node: [
                    (link["target"], link["value"])
                    for link in graph["outgoing"][node]
                ],
            )
    # Finish in the direction of flow so each column reflects the ordering of
    # the column immediately before it. This is especially important for
    # routing nodes, where a final right-to-left sweep can reintroduce a
    # crossing between two otherwise parallel ribbons.
    for depth in range(1, max_depth + 1):
        reorder(
            depth,
            lambda node: [
                (link["source"], link["value"])
                for link in graph["incoming"][node]
            ],
        )
    return columns


def _node_values(graph):
    values = {}
    for node in graph["nodes"]:
        incoming_value = sum(link["value"] for link in graph["incoming"][node])
        outgoing_value = sum(link["value"] for link in graph["outgoing"][node])
        values[node] = max(incoming_value, outgoing_value)
    return values


def _calculate_node_layout(
    graph,
    columns,
    height,
    node_width,
    node_padding,
    diagram_width,
    left_margin=24.0,
    right_margin=24.0,
    routing_nodes=None,
):
    top_margin = 36.0
    bottom_margin = 20.0
    values = _node_values(graph)
    scale_candidates = []
    for column in columns:
        available = (
            height
            - top_margin
            - bottom_margin
            - node_padding * max(0, len(column) - 1)
        )
        if available <= 0:
            raise ValueError(
                "Sankey height is too small for the requested node padding."
            )
        scale_candidates.append(available / sum(values[node] for node in column))
    scale = min(scale_candidates)

    max_depth = len(columns) - 1
    horizontal_space = diagram_width - left_margin - right_margin - node_width
    routing_nodes = routing_nodes or set()
    layout = {}
    for depth, column in enumerate(columns):
        x = left_margin + horizontal_space * depth / max_depth
        content_height = sum(values[node] * scale for node in column)
        content_height += node_padding * max(0, len(column) - 1)
        y = top_margin + (height - top_margin - bottom_margin - content_height) / 2
        for node in column:
            node_height = values[node] * scale
            layout[node] = {
                "x": x,
                "y": y,
                "width": 0 if node in routing_nodes else node_width,
                "height": node_height,
                "value": values[node],
                "depth": depth,
            }
            y += node_height + node_padding
    return layout, scale


def _calculate_link_layout(graph, node_layout, scale):
    source_offsets = {}
    target_offsets = {}
    for node in graph["nodes"]:
        geometry = node_layout[node]
        outgoing_height = sum(
            link["value"] * scale for link in graph["outgoing"][node]
        )
        incoming_height = sum(
            link["value"] * scale for link in graph["incoming"][node]
        )
        source_offsets[node] = geometry["y"] + (
            geometry["height"] - outgoing_height
        ) / 2
        target_offsets[node] = geometry["y"] + (
            geometry["height"] - incoming_height
        ) / 2

    source_bounds = {}
    target_bounds = {}
    for node in graph["nodes"]:
        for link in sorted(
            graph["outgoing"][node],
            key=lambda item: (
                node_layout[item["target"]]["y"],
                graph["order"][item["target"]],
            ),
        ):
            key = (link["source"], link["target"])
            top = source_offsets[node]
            bottom = top + link["value"] * scale
            source_bounds[key] = (top, bottom)
            source_offsets[node] = bottom

        for link in sorted(
            graph["incoming"][node],
            key=lambda item: (
                node_layout[item["source"]]["y"],
                graph["order"][item["source"]],
            ),
        ):
            key = (link["source"], link["target"])
            top = target_offsets[node]
            bottom = top + link["value"] * scale
            target_bounds[key] = (top, bottom)
            target_offsets[node] = bottom

    return [
        {
            **link,
            "source_top": source_bounds[(link["source"], link["target"])][0],
            "source_bottom": source_bounds[(link["source"], link["target"])][1],
            "target_top": target_bounds[(link["source"], link["target"])][0],
            "target_bottom": target_bounds[(link["source"], link["target"])][1],
        }
        for link in graph["links"]
    ]


def _parse_hex_color(color):
    if not isinstance(color, str):
        return None
    value = color.strip()
    if not value.startswith("#"):
        return None
    digits = value[1:]
    if len(digits) == 3:
        digits = "".join(character * 2 for character in digits)
    if len(digits) != 6:
        return None
    try:
        int(digits, 16)
    except ValueError:
        return None
    return f"#{digits.lower()}"


def _default_colors():
    candidates = [
        THEME.get("primary_color", "#007bff"),
        THEME.get("success_color", "#19b96c"),
        THEME.get("warning_color", "#f59e0b"),
        THEME.get("danger_color", "#dc3545"),
        THEME.get("accent_color", "#4c7cf0"),
    ]
    colors = []
    for color in candidates:
        if color not in colors:
            colors.append(color)
    return colors


def _resolve_node_colors(nodes, colors):
    defaults = _default_colors()
    if colors is None:
        palette = defaults
        mapping = {}
    elif isinstance(colors, dict):
        palette = defaults
        mapping = {}
        for raw_node, raw_color in colors.items():
            node = _normalize_label(raw_node, "color mapping")
            color = _parse_hex_color(raw_color)
            if color is None:
                raise ValueError("Sankey colors must be #RGB or #RRGGBB hex values.")
            mapping[node] = color
    elif isinstance(colors, (list, tuple)):
        if not colors:
            raise ValueError("Sankey colors cannot be an empty list.")
        palette = []
        for raw_color in colors:
            color = _parse_hex_color(raw_color)
            if color is None:
                raise ValueError("Sankey colors must be #RGB or #RRGGBB hex values.")
            palette.append(color)
        mapping = {}
    else:
        raise ValueError("Sankey colors must be a list, dictionary, or None.")

    return {
        node: mapping.get(node, palette[index % len(palette)])
        for index, node in enumerate(nodes)
    }


def _format_number(value, value_format=None):
    render_value = int(value) if float(value).is_integer() else value
    if value_format is not None:
        try:
            return format(render_value, value_format)
        except (TypeError, ValueError) as error:
            raise ValueError(
                f"Sankey value_format '{value_format}' is not valid."
            ) from error
    if isinstance(render_value, int):
        return f"{render_value:,}"
    return f"{render_value:,.6g}"


def _number(value):
    return f"{value:.3f}".rstrip("0").rstrip(".")


class Sankey:
    """Display prepared source-target-value flows as an SVG Sankey diagram.

    Parameters
    ----------
    data : pandas.DataFrame or list
        Flow rows supplied as a DataFrame, three-item tuples, or dictionaries.
    source, target, value : str, optional
        DataFrame column names or dictionary keys. Defaults are ``"source"``,
        ``"target"``, and ``"value"``.
    colors : list[str] or dict[str, str] or None, optional
        Hex node colors. Lists cycle through nodes; dictionaries map node names.
        Unmapped nodes use Mercury theme colors.
    height : int or float, optional
        SVG view-box height. Default is ``400``.
    node_width : int or float, optional
        Node rectangle width. Default is ``16``.
    node_padding : int or float, optional
        Vertical space between nodes in a column. Default is ``16``.
    link_opacity : float, optional
        Ribbon opacity between ``0`` and ``1``. Default is ``0.35``.
    show_values : bool, optional
        Append formatted values to visible node labels. Default is ``False``.
    value_format : str or None, optional
        Python numeric format specification, such as ``","``.

    Notes
    -----
    Duplicate links are summed and zero-value links are removed. The graph must
    be acyclic and cannot contain self-links. Rendering uses only HTML and SVG.
    """

    def __init__(
        self,
        data,
        source="source",
        target="target",
        value="value",
        colors=None,
        height=400,
        node_width=16,
        node_padding=16,
        link_opacity=0.35,
        show_values=False,
        value_format=None,
    ):
        self.height = self._positive_number(height, "height", minimum=120)
        self.node_width = self._positive_number(node_width, "node_width")
        self.node_padding = self._positive_number(
            node_padding, "node_padding", allow_zero=True
        )
        self.link_opacity = self._opacity(link_opacity)
        self.show_values = bool(show_values)
        if value_format is not None and not isinstance(value_format, str):
            raise ValueError("Sankey value_format must be a string or None.")
        if value_format is not None:
            _format_number(1.0, value_format)
        self.value_format = value_format

        self.links = _normalize_data(data, source, target, value)
        self.graph = _build_graph(self.links)
        self.topological_order = _topological_sort(self.graph)
        self.depths = _assign_depths(self.graph, self.topological_order)
        self.layout_graph, self.layout_depths, self.routing_nodes = (
            _expand_links_for_layout(self.graph, self.depths)
        )
        self.columns = _order_nodes(self.layout_graph, self.layout_depths)
        values = _node_values(self.graph)
        first_column_labels = [
            self._label_text(node, values[node]) for node in self.columns[0]
        ]
        final_column_labels = [
            self._label_text(node, values[node]) for node in self.columns[-1]
        ]
        self.left_margin = max(
            24.0,
            max(self._estimate_label_width(label) for label in first_column_labels)
            + 12,
        )
        self.right_margin = max(
            24.0,
            max(self._estimate_label_width(label) for label in final_column_labels)
            + 12,
        )
        self.diagram_width = max(
            600.0,
            len(self.columns) * 180.0
            + self.left_margin
            + self.right_margin
            - 48.0,
        )
        self.node_layout, self.scale = _calculate_node_layout(
            self.layout_graph,
            self.columns,
            self.height,
            self.node_width,
            self.node_padding,
            self.diagram_width,
            self.left_margin,
            self.right_margin,
            self.routing_nodes,
        )
        self.link_layout = _calculate_link_layout(
            self.layout_graph, self.node_layout, self.scale
        )
        self.node_colors = _resolve_node_colors(self.graph["nodes"], colors)

    def _label_text(self, node, value):
        formatted = _format_number(value, self.value_format)
        return f"{node} · {formatted}" if self.show_values else node

    @staticmethod
    def _estimate_label_width(label):
        return max(20.0, len(label) * 7.2)

    @staticmethod
    def _positive_number(raw, name, minimum=0, allow_zero=False):
        if isinstance(raw, bool) or not isinstance(raw, Real):
            raise ValueError(f"Sankey {name} must be numeric.")
        value = float(raw)
        valid = value >= minimum if allow_zero else value > minimum
        if not math.isfinite(value) or not valid:
            comparison = "at least" if allow_zero else "greater than"
            raise ValueError(f"Sankey {name} must be {comparison} {minimum}.")
        return value

    @staticmethod
    def _opacity(raw):
        if isinstance(raw, bool) or not isinstance(raw, Real):
            raise ValueError("Sankey link_opacity must be between 0 and 1.")
        value = float(raw)
        if not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError("Sankey link_opacity must be between 0 and 1.")
        return value

    def _styles(self):
        return """
<style>
.mljar-sankey {
    width: 100%%;
    max-width: 100%%;
    overflow-x: auto;
    color: %(text_color)s;
    font-family: %(font_family)s;
}
.mljar-sankey-svg {
    display: block;
    width: 100%%;
    min-width: %(minimum_width)spx;
    height: auto;
}
.mljar-sankey-link {
    transition: opacity 120ms ease;
}
.mljar-sankey-link:hover {
    opacity: 0.65;
}
.mljar-sankey-node {
    stroke: %(border_color)s;
    stroke-width: 1;
}
.mljar-sankey-label {
    fill: %(text_color)s;
    stroke: %(surface_color)s;
    stroke-width: 3px;
    paint-order: stroke;
    font-size: 12px;
    dominant-baseline: middle;
}
</style>""" % {
            "font_family": THEME.get("font_family", "Arial, sans-serif"),
            "text_color": THEME.get("text_color", "#0f172a"),
            "surface_color": THEME.get("surface_color", "#ffffff"),
            "border_color": THEME.get("border_color", "#d0d7de"),
            "minimum_width": _number(self.diagram_width),
        }

    def _link_svg(self, link):
        source = self.node_layout[link["source"]]
        target = self.node_layout[link["target"]]
        source_x = source["x"] + source["width"]
        target_x = target["x"]
        distance = target_x - source_x
        control_1 = source_x + distance * 0.45
        control_2 = target_x - distance * 0.45
        path = (
            f"M {_number(source_x)} {_number(link['source_top'])} "
            f"C {_number(control_1)} {_number(link['source_top'])}, "
            f"{_number(control_2)} {_number(link['target_top'])}, "
            f"{_number(target_x)} {_number(link['target_top'])} "
            f"L {_number(target_x)} {_number(link['target_bottom'])} "
            f"C {_number(control_2)} {_number(link['target_bottom'])}, "
            f"{_number(control_1)} {_number(link['source_bottom'])}, "
            f"{_number(source_x)} {_number(link['source_bottom'])} Z"
        )
        value = _format_number(link["value"], self.value_format)
        original_source = link.get("original_source", link["source"])
        original_target = link.get("original_target", link["target"])
        tooltip = f"{original_source} → {original_target}: {value}"
        return (
            '<path class="mljar-sankey-link" '
            f'd="{path}" fill="{self.node_colors[original_source]}" '
            f'opacity="{_number(self.link_opacity)}" '
            f'aria-label="{escape(tooltip, quote=True)}">'
            f"<title>{escape(tooltip)}</title></path>"
        )

    def _node_svg(self, node):
        geometry = self.node_layout[node]
        value = _format_number(geometry["value"], self.value_format)
        tooltip = f"{node} — {value}"
        is_first = geometry["depth"] == 0
        is_final = geometry["depth"] == len(self.columns) - 1
        label = self._label_text(node, geometry["value"])
        label_y = geometry["y"] + geometry["height"] / 2
        baseline = "middle"
        if is_first:
            label_x = geometry["x"] - 8
            anchor = "end"
        elif is_final:
            label_x = geometry["x"] + geometry["width"] + 8
            anchor = "start"
        else:
            label_x = geometry["x"] + geometry["width"] / 2
            label_y = geometry["y"] - 7
            anchor = "middle"
            baseline = "auto"
        return (
            f'<g class="mljar-sankey-node-group" role="img" '
            f'aria-label="{escape(tooltip, quote=True)}">'
            f'<rect class="mljar-sankey-node" x="{_number(geometry["x"])}" '
            f'y="{_number(geometry["y"])}" width="{_number(geometry["width"])}" '
            f'height="{_number(geometry["height"])}" rx="2" '
            f'fill="{self.node_colors[node]}"><title>{escape(tooltip)}</title></rect>'
            f'<text class="mljar-sankey-label" x="{_number(label_x)}" '
            f'y="{_number(label_y)}" text-anchor="{anchor}" '
            f'dominant-baseline="{baseline}">'
            f"{escape(label)}</text></g>"
        )

    def display(self):
        display(self)

    def _repr_html_(self):
        links = "".join(self._link_svg(link) for link in self.link_layout)
        nodes = "".join(self._node_svg(node) for node in self.graph["nodes"])
        node_count = len(self.graph["nodes"])
        flow_count = len(self.graph["links"])
        aria_label = f"Sankey diagram with {node_count} nodes and {flow_count} flows"
        svg = (
            f'<svg class="mljar-sankey-svg" '
            f'viewBox="0 0 {_number(self.diagram_width)} {_number(self.height)}" '
            f'role="img" aria-label="{aria_label}" '
            f'xmlns="http://www.w3.org/2000/svg">'
            "<title>Sankey diagram</title>"
            f"<desc>{aria_label}. Ribbon width represents flow value.</desc>"
            f"{links}{nodes}</svg>"
        )
        return f'{self._styles()}<div class="mljar-sankey">{svg}</div>'
