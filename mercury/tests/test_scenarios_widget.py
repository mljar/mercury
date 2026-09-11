import base64
import copy
import importlib
from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import mercury as mr
from mercury.manager import WidgetsManager
from mercury.number import NumberInputWidget
from mercury.scenarios import ScenariosWidget, _output
from mercury.select import SelectWidget

scenarios_module = importlib.import_module("mercury.scenarios")


@pytest.fixture
def component():
    growth = NumberInputWidget(value=5, min=0, max=30, source_cell_id="growth")
    price = NumberInputWidget(value=50, min=0, max=100, source_cell_id="price")
    widget = ScenariosWidget()
    widget.configure({"Growth": growth, "Price": price}, {"Revenue": 1000})
    yield widget, growth, price
    widget.close()


def test_snapshots_are_detached_and_inputs_invalidate_results(component):
    widget, growth, price = component
    saved = widget.snapshot("Baseline")
    growth.value = 15
    assert saved["inputs"]["Growth"] == 5
    with pytest.raises(ValueError, match="Inputs changed"):
        widget.snapshot("High growth")
    widget.configure({"Growth": growth, "Price": price}, {"Revenue": 2000})
    assert widget.snapshot("High growth")["outputs"]["Revenue"]["value"] == 2000
    assert saved["outputs"]["Revenue"]["value"] == 1000


def test_loading_validates_every_input_before_writing(component):
    widget, growth, price = component
    saved = widget.snapshot("Baseline")
    saved["inputs"].update(Growth=20, Price=200)
    with pytest.raises(ValueError, match="Price"):
        widget.load(saved)
    assert growth.value == 5
    assert price.value == 50


def test_load_ack_contains_changed_input_cells_once_and_preserves_snapshot(component):
    widget, growth, price = component
    saved = widget.snapshot("Baseline")
    original = copy.deepcopy(saved)
    growth.value, price.value = 15, 75
    widget.send = Mock()
    widget._handle_message(
        widget, {"event": "scenario_load", "request_id": "r", "snapshot": saved}, []
    )
    widget.send.assert_called_once_with(
        {
            "event": "scenario_loaded",
            "request_id": "r",
            "source_cell_ids": ["growth", "price"],
            "changed": True,
        }
    )
    assert (growth.value, price.value) == (5, 50)
    assert saved == original
    assert widget.load(saved) == ([], False)


def test_unexpected_assignment_failure_rolls_back(component):
    widget, growth, price = component
    saved = widget.snapshot("Baseline")
    saved["inputs"].update(Growth=20, Price=60)

    def reject(change):
        if change["new"] == 60:
            raise ValueError("rejected")

    price.observe(reject, names="value")
    with pytest.raises(ValueError, match="restored"):
        widget.load(saved)
    assert (growth.value, price.value) == (5, 50)


@pytest.mark.parametrize(
    "alter",
    [
        lambda s: s.update(version=2),
        lambda s: s["inputs"].pop("Price"),
        lambda s: s["input_types"].update(Growth="SliderWidget"),
    ],
)
def test_incompatible_scenario_rejected(component, alter):
    widget, growth, price = component
    saved = widget.snapshot("Baseline")
    alter(saved)
    with pytest.raises(ValueError):
        widget.load(saved)
    assert (growth.value, price.value) == (5, 50)


def test_changed_choices_and_disabled_inputs_rejected():
    choice = SelectWidget(value="A", choices=["A", "B"])
    widget = ScenariosWidget().configure({"Choice": choice}, {"Output": 1})
    saved = widget.snapshot("A")
    choice.choices, choice.value = ["B"], "B"
    with pytest.raises(ValueError, match="choices"):
        widget.load(saved)
    choice.disabled = True
    with pytest.raises(ValueError, match="disabled"):
        widget.load(saved)
    widget.close()


def test_successful_cell_required_and_failed_cell_invalidates(component):
    widget, growth, price = component
    widget._shell = SimpleNamespace(events=SimpleNamespace(unregister=Mock()))
    widget._before_cell()
    widget.configure({"Growth": growth}, {"Revenue": 100})
    assert not widget.ready
    widget._after_cell(SimpleNamespace(error_before_exec=None, error_in_exec=None))
    assert widget.ready
    widget._before_cell()
    with pytest.raises(ValueError):
        widget.snapshot("While running")
    widget._after_cell(
        SimpleNamespace(error_before_exec=None, error_in_exec=RuntimeError())
    )
    with pytest.raises(ValueError, match="failed"):
        widget.snapshot("Failed")


def test_factory_keeps_identity_when_values_and_outputs_change(monkeypatch):
    monkeypatch.setattr(scenarios_module, "display", Mock())
    widget_input = NumberInputWidget(value=1)
    first = mr.Scenarios(
        {"Input": widget_input}, {"Value": 2}, key="stable-scenarios-test"
    )
    saved = first.snapshot("Original")
    widget_input.value = 3
    second = mr.Scenarios(
        {"Input": widget_input}, {"Value": 6}, key="stable-scenarios-test"
    )
    assert second is first
    assert saved["outputs"]["Value"]["value"] == 2
    assert first.snapshot("New")["outputs"]["Value"]["value"] == 6
    first.close()
    for uid in list(WidgetsManager.widgets):
        if WidgetsManager.widgets[uid] is first:
            del WidgetsManager.widgets[uid]


def test_pandas_table_preserves_order_types_index_and_snapshot():
    pd = pytest.importorskip("pandas")
    df = pd.DataFrame(
        {"Day": [date(2026, 1, 1)], "Revenue": [42.5], "Count": [2**60]},
        index=["January"],
    )
    saved = _output(df)
    df.loc["January", "Revenue"] = 0
    assert saved["columns"] == ["Day", "Revenue", "Count"]
    assert saved["rows"] == [
        [
            {"type": "date", "value": "2026-01-01"},
            42.5,
            {"type": "integer", "value": str(2**60)},
        ]
    ]
    assert saved["index"] == ["January"]


def test_polars_table():
    pl = pytest.importorskip("polars")
    saved = _output(pl.DataFrame({"Month": ["Jan", "Feb"], "Revenue": [100, 200]}))
    assert saved["columns"] == ["Month", "Revenue"]
    assert saved["rows"] == [["Jan", 100], ["Feb", 200]]


def test_matplotlib_figure_and_axes_are_png_snapshots():
    pytest.importorskip("matplotlib")
    from matplotlib.figure import Figure

    figure = Figure()
    axes = figure.subplots()
    axes.plot([1, 2], [3, 4])
    saved = _output(figure)
    assert base64.b64decode(saved["data"]).startswith(b"\x89PNG\r\n\x1a\n")
    axes.plot([1, 2], [5, 6])
    assert _output(axes)["data"] != saved["data"]


def test_size_and_unsupported_output_errors_block_saving(component, monkeypatch):
    widget, growth, price = component
    widget.configure({"Growth": growth}, {"Unsupported": object()})
    assert "Unsupported" in widget.error
    with pytest.raises(ValueError):
        widget.snapshot("Unsupported")
    monkeypatch.setattr(scenarios_module, "MAX_SNAPSHOT_BYTES", 100)
    widget.configure({"Growth": growth}, {"Large": "a" * 101})
    assert "limit" in widget.error
    assert not widget.ready


def test_tables_exceeding_limits_are_not_truncated():
    pd = pytest.importorskip("pandas")
    with pytest.raises(ValueError, match="limited"):
        _output(pd.DataFrame({"x": range(5001)}))
