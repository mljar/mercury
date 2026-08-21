import mercury.columns as columns_module
import mercury.expander as expander_module
import mercury.tabs as tabs_module
from mercury.columns import Columns
from mercury.expander import Expander
from mercury.manager import WidgetsManager
from mercury.render_context import get_render_context, source_cell_context
from mercury.tabs import Tabs


def _disable_display(monkeypatch):
    monkeypatch.setattr(columns_module, "display", lambda *_: None)
    monkeypatch.setattr(expander_module, "display", lambda *_: None)
    monkeypatch.setattr(tabs_module, "display", lambda *_: None)


def setup_function():
    WidgetsManager.clear()


def teardown_function():
    WidgetsManager.clear()


def test_source_cell_context_sets_current_cell_id():
    assert get_render_context().source_cell_id is None
    assert get_render_context().render_slot_id is None
    assert get_render_context().layout_path is None

    with source_cell_context("cell-123"):
        assert get_render_context().source_cell_id == "cell-123"
        assert get_render_context().layout_stack == ()
        assert get_render_context().render_slot_id is None
        assert get_render_context().layout_path is None

    assert get_render_context().source_cell_id is None


def test_nested_layout_outputs_build_render_context_stack(monkeypatch):
    _disable_display(monkeypatch)

    with source_cell_context("cell-42"):
        tabs = Tabs(labels=["a"])
        with tabs[0]:
            tabs_ctx = get_render_context()
            tabs_slot_id = tabs_ctx.layout_stack[-1].slot_id

            cols = Columns(2)
            with cols[1]:
                cols_ctx = get_render_context()
                cols_slot_id = cols_ctx.layout_stack[-1].slot_id

                exp = Expander("Details")
                with exp:
                    exp_ctx = get_render_context()
                    exp_slot_id = exp_ctx.layout_stack[-1].slot_id

    assert tabs_ctx.source_cell_id == "cell-42"
    assert [frame.layout_type for frame in tabs_ctx.layout_stack] == ["tabs"]
    assert tabs_ctx.render_slot_id == tabs_slot_id
    assert tabs_ctx.layout_path == tabs_slot_id

    assert cols_ctx.source_cell_id == "cell-42"
    assert [frame.layout_type for frame in cols_ctx.layout_stack] == [
        "tabs",
        "columns",
    ]
    assert cols_ctx.render_slot_id == cols_slot_id
    assert cols_ctx.layout_path == f"{tabs_slot_id}/{cols_slot_id}"

    assert exp_ctx.source_cell_id == "cell-42"
    assert [frame.layout_type for frame in exp_ctx.layout_stack] == [
        "tabs",
        "columns",
        "expander",
    ]
    assert exp_ctx.render_slot_id == exp_slot_id
    assert exp_ctx.layout_path == f"{tabs_slot_id}/{cols_slot_id}/{exp_slot_id}"


def test_columns_clears_cached_outputs_by_default(monkeypatch):
    _disable_display(monkeypatch)

    outs = Columns(2)
    calls = []

    for idx, out in enumerate(outs):
        monkeypatch.setattr(
            out,
            "clear_output",
            lambda wait=True, idx=idx: calls.append((idx, wait)),
        )

    reused = Columns(2)

    assert reused is outs
    assert calls == [(0, True), (1, True)]


def test_columns_append_true_preserves_cached_outputs(monkeypatch):
    _disable_display(monkeypatch)

    outs = Columns(2)
    calls = []

    for out in outs:
        monkeypatch.setattr(
            out,
            "clear_output",
            lambda wait=True: calls.append(wait),
        )

    reused = Columns(2, append=True)

    assert reused is outs
    assert calls == []


def test_columns_default_clear_resets_output_buffers(monkeypatch):
    _disable_display(monkeypatch)
    WidgetsManager.widgets.clear()

    outs = Columns(2)
    outs[0].append_stdout("first\n")
    outs[1].append_stdout("second\n")

    reused = Columns(2)

    assert reused is outs
    assert reused[0].outputs == ()
    assert reused[1].outputs == ()


def test_columns_append_true_preserves_output_buffers(monkeypatch):
    _disable_display(monkeypatch)
    WidgetsManager.widgets.clear()

    outs = Columns(2)
    outs[0].append_stdout("first\n")
    outs[1].append_stdout("second\n")

    reused = Columns(2, append=True)

    assert reused is outs
    assert len(reused[0].outputs) == 1
    assert len(reused[1].outputs) == 1


def test_columns_clear_method_resets_output_buffer(monkeypatch):
    _disable_display(monkeypatch)
    WidgetsManager.widgets.clear()

    outs = Columns(2)
    calls = []
    monkeypatch.setattr(outs[0], "clear_output", lambda wait=True: calls.append(wait))
    outs[0].append_stdout("first\n")

    outs[0].clear(wait=False)

    assert calls == [False]
    assert outs[0].outputs == ()


def test_columns_accepts_proportional_widths(monkeypatch):
    _disable_display(monkeypatch)
    WidgetsManager.widgets.clear()

    left, right = Columns([0.4, 0.6])

    assert left.layout.flex == "0.4 1 0px"
    assert right.layout.flex == "0.6 1 0px"


def test_columns_default_layout_wraps_at_a_mobile_friendly_width(monkeypatch):
    _disable_display(monkeypatch)

    columns = Columns(2)
    box, _ = next(iter(WidgetsManager.widgets.values()))

    assert box.layout.flex_flow == "row wrap"
    assert "mljar-columns" in box._dom_classes
    assert all(
        column.layout.min_width == "min(260px, 100%)" for column in columns
    )
    assert all(column.layout.max_width == "100%" for column in columns)
    assert all(column.layout.box_sizing == "border-box" for column in columns)


def test_columns_preserves_explicit_minimum_width(monkeypatch):
    _disable_display(monkeypatch)

    columns = Columns(2, min_width="180px")

    assert all(column.layout.min_width == "180px" for column in columns)


def test_columns_accepts_integer_like_width_ratios(monkeypatch):
    _disable_display(monkeypatch)
    WidgetsManager.widgets.clear()

    cols = Columns([1, 2, 1])

    assert len(cols) == 3
    assert [col.layout.flex for col in cols] == [
        "1 1 0px",
        "2 1 0px",
        "1 1 0px",
    ]


def test_columns_equal_count_and_width_specs_have_different_cache_keys(monkeypatch):
    _disable_display(monkeypatch)
    WidgetsManager.widgets.clear()

    equal = Columns(2)
    weighted = Columns([0.4, 0.6])

    assert equal is not weighted
    assert len(WidgetsManager.widgets) == 2


def test_columns_rejects_empty_width_list():
    WidgetsManager.widgets.clear()

    try:
        Columns([])
    except Exception as exc:
        assert "must not be empty" in str(exc)
    else:
        raise AssertionError("Columns([]) should fail")


def test_columns_rejects_non_positive_widths():
    WidgetsManager.widgets.clear()

    try:
        Columns([0.4, 0])
    except Exception as exc:
        assert "greater than 0" in str(exc)
    else:
        raise AssertionError("Columns([0.4, 0]) should fail")


def test_columns_rejects_non_numeric_widths():
    WidgetsManager.widgets.clear()

    try:
        Columns([0.4, "wide"])
    except Exception as exc:
        assert "must be numbers" in str(exc)
    else:
        raise AssertionError('Columns([0.4, "wide"]) should fail')


def test_tabs_clears_cached_outputs_by_default(monkeypatch):
    _disable_display(monkeypatch)

    outs = Tabs(labels=["a", "b"])
    calls = []

    for idx, out in enumerate(outs):
        monkeypatch.setattr(
            out,
            "clear_output",
            lambda wait=True, idx=idx: calls.append((idx, wait)),
        )

    reused = Tabs(labels=["a", "b"])

    assert reused is outs
    assert calls == [(0, True), (1, True)]


def test_tabs_append_true_preserves_cached_outputs(monkeypatch):
    _disable_display(monkeypatch)

    outs = Tabs(labels=["a", "b"])
    calls = []

    for out in outs:
        monkeypatch.setattr(
            out,
            "clear_output",
            lambda wait=True: calls.append(wait),
        )

    reused = Tabs(labels=["a", "b"], append=True)

    assert reused is outs
    assert calls == []


def test_tabs_default_clear_resets_output_buffers(monkeypatch):
    _disable_display(monkeypatch)
    WidgetsManager.widgets.clear()

    outs = Tabs(labels=["a", "b"])
    outs[0].append_stdout("first\n")
    outs[1].append_stdout("second\n")

    reused = Tabs(labels=["a", "b"])

    assert reused is outs
    assert reused[0].outputs == ()
    assert reused[1].outputs == ()


def test_tabs_append_true_preserves_output_buffers(monkeypatch):
    _disable_display(monkeypatch)
    WidgetsManager.widgets.clear()

    outs = Tabs(labels=["a", "b"])
    outs[0].append_stdout("first\n")
    outs[1].append_stdout("second\n")

    reused = Tabs(labels=["a", "b"], append=True)

    assert reused is outs
    assert len(reused[0].outputs) == 1
    assert len(reused[1].outputs) == 1


def test_tabs_clear_method_resets_output_buffer(monkeypatch):
    _disable_display(monkeypatch)
    WidgetsManager.widgets.clear()

    outs = Tabs(labels=["a", "b"])
    calls = []
    monkeypatch.setattr(outs[0], "clear_output", lambda wait=True: calls.append(wait))
    outs[0].append_stdout("first\n")

    outs[0].clear(wait=False)

    assert calls == [False]
    assert outs[0].outputs == ()


def test_expander_clears_cached_output_by_default(monkeypatch):
    _disable_display(monkeypatch)

    out = Expander("Details")
    calls = []
    monkeypatch.setattr(out, "clear_output", lambda wait=True: calls.append(wait))

    reused = Expander("Details")

    assert reused is out
    assert calls == [True]


def test_expander_append_true_preserves_cached_output(monkeypatch):
    _disable_display(monkeypatch)

    out = Expander("Details")
    calls = []
    monkeypatch.setattr(out, "clear_output", lambda wait=True: calls.append(wait))

    reused = Expander("Details", append=True)

    assert reused is out
    assert calls == []


def test_expander_default_clear_resets_output_buffer(monkeypatch):
    _disable_display(monkeypatch)
    WidgetsManager.widgets.clear()

    out = Expander("Details")
    out.append_stdout("first\n")
    assert len(out.outputs) == 1

    reused = Expander("Details")

    assert reused is out
    assert reused.outputs == ()


def test_expander_append_true_preserves_output_buffer(monkeypatch):
    _disable_display(monkeypatch)
    WidgetsManager.widgets.clear()

    out = Expander("Details")
    out.append_stdout("first\n")
    assert len(out.outputs) == 1

    reused = Expander("Details", append=True)

    assert reused is out
    assert len(reused.outputs) == 1


def test_expander_clear_method_resets_output_buffer(monkeypatch):
    _disable_display(monkeypatch)
    WidgetsManager.widgets.clear()

    out = Expander("Details")
    calls = []
    monkeypatch.setattr(out, "clear_output", lambda wait=True: calls.append(wait))
    out.append_stdout("first\n")

    out.clear(wait=False)

    assert calls == [False]
    assert out.outputs == ()


def test_expander_default_style_preserves_border_and_header_background(monkeypatch):
    _disable_display(monkeypatch)
    WidgetsManager.widgets.clear()

    Expander("Details")
    box, _out, header, _content_box = next(
        value
        for key, value in WidgetsManager.widgets.items()
        if key.startswith("Expander.")
    )

    assert "is-borderless" not in box._dom_classes
    assert header.header_background is True


def test_expander_can_disable_border_and_header_background(monkeypatch):
    _disable_display(monkeypatch)
    WidgetsManager.widgets.clear()

    Expander("Plain", show_border=False, header_background=False)
    box, _out, header, _content_box = next(
        value
        for key, value in WidgetsManager.widgets.items()
        if key.startswith("Expander.")
    )

    assert "is-borderless" in box._dom_classes
    assert header.header_background is False


def test_expander_style_flags_are_part_of_cache_key(monkeypatch):
    _disable_display(monkeypatch)
    WidgetsManager.widgets.clear()

    bordered = Expander("Details", show_border=True, header_background=True)
    plain = Expander("Details", show_border=False, header_background=False)

    assert bordered is not plain
    expander_keys = [
        key for key in WidgetsManager.widgets.keys() if key.startswith("Expander.")
    ]
    assert len(expander_keys) == 2
