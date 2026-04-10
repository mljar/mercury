import pytest
from traitlets import TraitError

import mercury.number as m
from mercury.number import NumberInput
from mercury.number import NumberInputWidget
from mercury.manager import WidgetsManager
from mercury.url_params import clear_runtime_url_params, set_runtime_url_params


# --- NumberInput general behaviour ------------------------------------------------


def test_numberinput_defaults_value_to_min_when_none():
    widget = NumberInput(label="Rows", value=None, min=5, max=10, step=1)
    assert widget.value == 5.0


def test_numberinput_preserves_valid_value_in_range():
    w = NumberInputWidget(value=7.5, min=0.0, max=10.0, step=0.5)
    assert w.value == 7.5


def test_numberinput_clamps_value_below_min():
    w = NumberInputWidget(value=-2.0, min=1.0, max=10.0, step=1.0)
    assert w.value == 1.0


def test_numberinput_clamps_value_above_max():
    w = NumberInputWidget(value=20.0, min=1.0, max=10.0, step=1.0)
    assert w.value == 10.0


def test_numberinput_swaps_min_and_max_when_reversed():
    with pytest.warns(UserWarning, match="min.*greater than.*max"):
        widget = NumberInput(label="Rows", value=5, min=10, max=1)
    assert widget.min == 1.0
    assert widget.max == 10.0


def test_numberinput_invalid_step_defaults_to_one(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()

    with pytest.warns(UserWarning, match="step.*not a number.*Defaulting to 1"):
        widget = NumberInput(label="Rows", value=5, min=0, max=10, step="abc")

    assert widget.step == 1.0


def test_numberinput_invalid_value_defaults_to_min(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()

    with pytest.warns(UserWarning, match="value.*not a number.*Defaulting to `min`"):
        widget = NumberInput(label="Rows", value="abc", min=2, max=10, step=1)

    assert widget.value == 2.0


# --- NumberInput url_params -------------------------------------------------------


def test_numberinput_uses_integer_url_param_when_valid(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()
    clear_runtime_url_params()
    set_runtime_url_params({"rows": ["7"]})

    widget = NumberInput(
        label="Rows",
        value=2,
        min=0,
        max=10,
        step=1,
        url_key="rows",
    )

    assert widget.value == 7.0


def test_numberinput_uses_float_url_param_and_snaps_to_step(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()
    clear_runtime_url_params()
    set_runtime_url_params({"rows": ["1.25"]})

    widget = NumberInput(
        label="Rows",
        value=2,
        min=1,
        max=10,
        step=0.1,
        url_key="rows",
    )

    assert widget.value == 1.3


def test_numberinput_falls_back_to_value_when_url_param_empty(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()
    clear_runtime_url_params()
    set_runtime_url_params({"rows": [""]})

    widget = NumberInput(
        label="Rows",
        value=4,
        min=0,
        max=10,
        step=1,
        url_key="rows",
    )

    assert widget.value == 4.0


def test_numberinput_falls_back_to_value_when_url_param_invalid(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()
    clear_runtime_url_params()
    set_runtime_url_params({"rows": ["abc"]})

    widget = NumberInput(
        label="Rows",
        value=4,
        min=0,
        max=10,
        step=1,
        url_key="rows",
    )

    assert widget.value == 4.0


def test_numberinput_clamps_url_param_below_min(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()
    clear_runtime_url_params()
    set_runtime_url_params({"rows": ["-5"]})

    widget = NumberInput(
        label="Rows",
        value=4,
        min=1,
        max=10,
        step=1,
        url_key="rows",
    )

    assert widget.value == 1.0


def test_numberinput_clamps_url_param_above_max(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()
    clear_runtime_url_params()
    set_runtime_url_params({"rows": ["50"]})

    widget = NumberInput(
        label="Rows",
        value=4,
        min=1,
        max=10,
        step=1,
        url_key="rows",
    )

    assert widget.value == 10.0


def test_numberinput_url_param_tie_rounds_up(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()
    clear_runtime_url_params()
    set_runtime_url_params({"rows": ["1.25"]})

    widget = NumberInput(
        label="Rows",
        value=4,
        min=1,
        max=10,
        step=0.1,
        url_key="rows",
    )

    assert widget.value == 1.3


def test_numberinput_url_param_step_snaps_from_min(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()
    clear_runtime_url_params()
    set_runtime_url_params({"rows": ["2.2"]})

    widget = NumberInput(
        label="Rows",
        value=4,
        min=1.5,
        max=10,
        step=0.5,
        url_key="rows",
    )

    assert widget.value == 2.0


# --- Trait defaults & validation --------------------------------------------------


def test_numberinput_trait_defaults():
    w = NumberInputWidget()
    assert w.label == "Enter number"
    assert w.disabled is False
    assert w.hidden is False
    assert w.position == "sidebar"


def test_numberinput_invalid_position_raises_traiterror():
    w = NumberInputWidget()
    with pytest.raises(TraitError):
        w.position = "top"


# --- _repr_mimebundle_ / MERCURY_MIMETYPE integration ----------------------------


def test_numberinput_repr_mimebundle_adds_mercury_metadata(monkeypatch):
    base_result = [
        {"text/plain": "foo", "application/vnd.jupyter.widget-view+json": {}},
        {"something_else": "bar"},
    ]

    def fake_super_repr(self, **kwargs):
        return [dict(base_result[0]), dict(base_result[1])]

    monkeypatch.setattr(m.anywidget.AnyWidget, "_repr_mimebundle_", fake_super_repr)

    widget = NumberInputWidget(position="inline")
    data = widget._repr_mimebundle_()

    assert len(data) == 2
    assert m.MERCURY_MIMETYPE in data[0]
    metadata = data[0][m.MERCURY_MIMETYPE]
    assert metadata["widget"] == type(widget).__qualname__
    assert metadata["position"] == "inline"
    assert isinstance(metadata["model_id"], str)
    assert metadata["model_id"]
    assert "text/plain" not in data[0]


def test_numberinput_repr_mimebundle_not_modified_when_single_mimetype(monkeypatch):
    base_result = [{"text/plain": "foo"}]

    def fake_super_repr(self, **kwargs):
        return [dict(base_result[0])]

    monkeypatch.setattr(m.anywidget.AnyWidget, "_repr_mimebundle_", fake_super_repr)

    widget = NumberInputWidget()
    data = widget._repr_mimebundle_()

    assert data == base_result
