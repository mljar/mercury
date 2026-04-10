import pytest
from traitlets import TraitError

import mercury.slider as m
from mercury.slider import Slider
from mercury.slider import SliderWidget
from mercury.manager import WidgetsManager
from mercury.url_params import clear_runtime_url_params, set_runtime_url_params


# --- Slider general behaviour -----------------------------------------------------


def test_slider_defaults_value_to_min_when_none(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()

    widget = Slider(label="Rows", value=None, min=5, max=10)

    assert widget.value == 5


def test_slider_preserves_valid_value_in_range(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()

    widget = Slider(label="Rows", value=7, min=0, max=10)

    assert widget.value == 7


def test_slider_clamps_value_below_min(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()

    with pytest.warns(UserWarning, match="value.*out of range.*Clamping"):
        widget = Slider(label="Rows", value=-2, min=1, max=10)

    assert widget.value == 1


def test_slider_clamps_value_above_max(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()

    with pytest.warns(UserWarning, match="value.*out of range.*Clamping"):
        widget = Slider(label="Rows", value=20, min=1, max=10)

    assert widget.value == 10


def test_slider_swaps_min_and_max_when_reversed(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()

    with pytest.warns(UserWarning, match="min.*greater than.*max"):
        widget = Slider(label="Rows", value=5, min=10, max=1)

    assert widget.min == 1
    assert widget.max == 10


def test_slider_invalid_value_defaults_to_min(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()

    with pytest.warns(UserWarning, match="value.*not an integer.*Defaulting to `min`"):
        widget = Slider(label="Rows", value="abc", min=2, max=10)

    assert widget.value == 2


# --- Slider url_params ------------------------------------------------------------


def test_slider_uses_integer_url_param_when_valid(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()
    clear_runtime_url_params()
    set_runtime_url_params({"rows": ["7"]})

    widget = Slider(
        label="Rows",
        value=2,
        min=0,
        max=10,
        url_key="rows",
    )

    assert widget.value == 7


def test_slider_falls_back_to_value_when_url_param_missing(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()
    clear_runtime_url_params()

    widget = Slider(
        label="Rows",
        value=4,
        min=0,
        max=10,
        url_key="rows",
    )

    assert widget.value == 4


def test_slider_falls_back_to_value_when_url_param_empty(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()
    clear_runtime_url_params()
    set_runtime_url_params({"rows": [""]})

    widget = Slider(
        label="Rows",
        value=4,
        min=0,
        max=10,
        url_key="rows",
    )

    assert widget.value == 4


def test_slider_falls_back_to_value_when_url_param_invalid(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()
    clear_runtime_url_params()
    set_runtime_url_params({"rows": ["abc"]})

    widget = Slider(
        label="Rows",
        value=4,
        min=0,
        max=10,
        url_key="rows",
    )

    assert widget.value == 4


def test_slider_falls_back_to_value_when_url_param_is_float(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()
    clear_runtime_url_params()
    set_runtime_url_params({"rows": ["4.5"]})

    widget = Slider(
        label="Rows",
        value=4,
        min=0,
        max=10,
        url_key="rows",
    )

    assert widget.value == 4


def test_slider_clamps_url_param_below_min(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()
    clear_runtime_url_params()
    set_runtime_url_params({"rows": ["-5"]})

    widget = Slider(
        label="Rows",
        value=4,
        min=1,
        max=10,
        url_key="rows",
    )

    assert widget.value == 1


def test_slider_clamps_url_param_above_max(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()
    clear_runtime_url_params()
    set_runtime_url_params({"rows": ["50"]})

    widget = Slider(
        label="Rows",
        value=4,
        min=1,
        max=10,
        url_key="rows",
    )

    assert widget.value == 10


# --- Trait defaults & validation --------------------------------------------------


def test_slider_trait_defaults():
    w = SliderWidget()
    assert w.label == "Select number"
    assert w.disabled is False
    assert w.hidden is False
    assert w.position == "sidebar"


def test_slider_invalid_position_raises_traiterror():
    w = SliderWidget()
    with pytest.raises(TraitError):
        w.position = "top"


# --- _repr_mimebundle_ / MERCURY_MIMETYPE integration ----------------------------


def test_slider_repr_mimebundle_adds_mercury_metadata(monkeypatch):
    base_result = [
        {"text/plain": "foo", "application/vnd.jupyter.widget-view+json": {}},
        {"something_else": "bar"},
    ]

    def fake_super_repr(self, **kwargs):
        return [dict(base_result[0]), dict(base_result[1])]

    monkeypatch.setattr(m.anywidget.AnyWidget, "_repr_mimebundle_", fake_super_repr)

    widget = SliderWidget(position="inline")
    data = widget._repr_mimebundle_()

    assert len(data) == 2
    assert m.MERCURY_MIMETYPE in data[0]
    metadata = data[0][m.MERCURY_MIMETYPE]
    assert metadata["widget"] == type(widget).__qualname__
    assert metadata["position"] == "inline"
    assert isinstance(metadata["model_id"], str)
    assert metadata["model_id"]
    assert "text/plain" not in data[0]


def test_slider_repr_mimebundle_not_modified_when_single_mimetype(monkeypatch):
    base_result = [{"text/plain": "foo"}]

    def fake_super_repr(self, **kwargs):
        return [dict(base_result[0])]

    monkeypatch.setattr(m.anywidget.AnyWidget, "_repr_mimebundle_", fake_super_repr)

    widget = SliderWidget()
    data = widget._repr_mimebundle_()

    assert data == base_result
