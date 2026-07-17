import pytest
from traitlets import TraitError

import mercury.text as m
from mercury.text import TextInput
from mercury.text import TextInputWidget
from mercury.manager import WidgetsManager
from mercury.url_params import clear_runtime_url_params, set_runtime_url_params


# --- TextInput general behaviour --------------------------------------------------


def test_textinput_preserves_explicit_value():
    widget = TextInputWidget(value="hello")
    assert widget.value == "hello"


def test_textinput_trait_defaults():
    w = TextInputWidget()
    assert w.label == "Enter text"
    assert w.disabled is False
    assert w.hidden is False
    assert w.position == "sidebar"


def test_textinput_passes_disabled_and_hidden_to_widget(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()

    widget = TextInput(
        label="Enter username",
        value="jan",
        disabled=True,
        hidden=True,
    )

    assert widget.disabled is True
    assert widget.hidden is True


def test_textinput_default_rows_is_single_line():
    w = TextInputWidget()
    assert w.rows == 1


def test_textinput_passes_rows_to_widget(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()

    widget = TextInput(label="Notes", rows=5)

    assert widget.rows == 5


def test_textinput_rows_must_be_positive():
    w = TextInputWidget()
    with pytest.raises(TraitError):
        w.rows = 0


def test_textinput_multiline_renders_textarea():
    esm = TextInputWidget._esm
    assert "textarea" in esm

    css = TextInputWidget._css
    assert "textarea.mljar-textinput-input" in css
    assert "resize: vertical;" in css


def test_textinput_invalid_position_raises_traiterror():
    w = TextInputWidget()
    with pytest.raises(TraitError):
        w.position = "top"


def test_textinput_focus_keeps_constant_border_width():
    css = TextInputWidget._css

    assert ".mljar-textinput-input:focus" in css
    assert "border-width: 2px;" not in css


# --- TextInput url_params ---------------------------------------------------------


def test_textinput_uses_url_param_value_when_valid(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()
    clear_runtime_url_params()
    set_runtime_url_params({"username": ["jan"]})

    widget = TextInput(
        label="Enter username",
        value="default",
        url_key="username",
    )

    assert widget.value == "jan"


def test_textinput_falls_back_to_value_when_url_param_missing(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()
    clear_runtime_url_params()

    widget = TextInput(
        label="Enter username",
        value="default",
        url_key="username",
    )

    assert widget.value == "default"


def test_textinput_falls_back_to_value_when_url_param_empty(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()
    clear_runtime_url_params()
    set_runtime_url_params({"username": [""]})

    widget = TextInput(
        label="Enter username",
        value="default",
        url_key="username",
    )

    assert widget.value == "default"


def test_textinput_falls_back_to_value_when_url_param_is_whitespace(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()
    clear_runtime_url_params()
    set_runtime_url_params({"username": ["   "]})

    widget = TextInput(
        label="Enter username",
        value="default",
        url_key="username",
    )

    assert widget.value == "default"


# --- _repr_mimebundle_ / MERCURY_MIMETYPE integration ----------------------------


def test_textinput_repr_mimebundle_adds_mercury_metadata(monkeypatch):
    base_result = [
        {"text/plain": "foo", "application/vnd.jupyter.widget-view+json": {}},
        {"something_else": "bar"},
    ]

    def fake_super_repr(self, **kwargs):
        return [dict(base_result[0]), dict(base_result[1])]

    monkeypatch.setattr(m.anywidget.AnyWidget, "_repr_mimebundle_", fake_super_repr)

    widget = TextInputWidget(position="inline")
    data = widget._repr_mimebundle_()

    assert len(data) == 2
    assert m.MERCURY_MIMETYPE in data[0]
    metadata = data[0][m.MERCURY_MIMETYPE]
    assert metadata["widget"] == type(widget).__qualname__
    assert metadata["position"] == "inline"
    assert isinstance(metadata["model_id"], str)
    assert metadata["model_id"]
    assert "text/plain" not in data[0]


def test_textinput_repr_mimebundle_not_modified_when_single_mimetype(monkeypatch):
    base_result = [{"text/plain": "foo"}]

    def fake_super_repr(self, **kwargs):
        return [dict(base_result[0])]

    monkeypatch.setattr(m.anywidget.AnyWidget, "_repr_mimebundle_", fake_super_repr)

    widget = TextInputWidget()
    data = widget._repr_mimebundle_()

    assert data == base_result
