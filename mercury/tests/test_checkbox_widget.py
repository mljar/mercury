import pytest
from traitlets import TraitError

import mercury.checkbox as m
from mercury.checkbox import CheckBox, CheckboxWidget
from mercury.manager import WidgetsManager
from mercury.url_params import clear_runtime_url_params, set_runtime_url_params


def test_checkbox_preserves_true_value(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()

    widget = CheckBox(label="Enable feature", value=True)

    assert widget.value is True


def test_checkbox_preserves_false_value(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()

    widget = CheckBox(label="Enable feature", value=False)

    assert widget.value is False


def test_checkbox_defaults():
    widget = CheckboxWidget()

    assert widget.label == "Enable"
    assert widget.value is False
    assert widget.disabled is False
    assert widget.hidden is False
    assert widget.position == "sidebar"
    assert widget.appearance == "toggle"


def test_checkbox_invalid_position_raises():
    with pytest.raises(TraitError):
        CheckboxWidget(position="left")


def test_checkbox_invalid_appearance_raises():
    with pytest.raises(TraitError):
        CheckboxWidget(appearance="pill")


def test_checkbox_uses_true_url_param(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()
    clear_runtime_url_params()
    set_runtime_url_params({"enabled": ["true"]})

    widget = CheckBox(label="Enable feature", value=False, url_key="enabled")

    assert widget.value is True


def test_checkbox_uses_false_url_param(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()
    clear_runtime_url_params()
    set_runtime_url_params({"enabled": ["false"]})

    widget = CheckBox(label="Enable feature", value=True, url_key="enabled")

    assert widget.value is False


def test_checkbox_falls_back_to_value_when_url_param_missing(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()
    clear_runtime_url_params()

    widget = CheckBox(label="Enable feature", value=True, url_key="enabled")

    assert widget.value is True


def test_checkbox_falls_back_to_value_when_url_param_empty(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()
    clear_runtime_url_params()
    set_runtime_url_params({"enabled": [""]})

    widget = CheckBox(label="Enable feature", value=True, url_key="enabled")

    assert widget.value is True


def test_checkbox_falls_back_to_value_when_url_param_invalid(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()
    clear_runtime_url_params()
    set_runtime_url_params({"enabled": ["1"]})

    widget = CheckBox(label="Enable feature", value=False, url_key="enabled")

    assert widget.value is False


def test_checkbox_matches_url_param_case_insensitively(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()
    clear_runtime_url_params()
    set_runtime_url_params({"enabled": ["TRUE"]})

    widget = CheckBox(label="Enable feature", value=False, url_key="enabled")

    assert widget.value is True


def test_repr_mimebundle_adds_mercury_metadata(monkeypatch):
    base_result = [
        {"text/plain": "foo", "application/vnd.jupyter.widget-view+json": {}},
        {"something_else": "bar"},
    ]

    def fake_super_repr(self, **kwargs):
        return [dict(base_result[0]), dict(base_result[1])]

    monkeypatch.setattr(m.anywidget.AnyWidget, "_repr_mimebundle_", fake_super_repr)

    widget = CheckboxWidget(position="inline")
    data = widget._repr_mimebundle_()

    assert len(data) == 2
    assert m.MERCURY_MIMETYPE in data[0]

    metadata = data[0][m.MERCURY_MIMETYPE]
    assert metadata["widget"] == type(widget).__qualname__
    assert metadata["position"] == "inline"
    assert isinstance(metadata["model_id"], str)
    assert metadata["model_id"]
    assert "text/plain" not in data[0]


def test_repr_mimebundle_not_modified_when_single_mimetype(monkeypatch):
    base_result = [{"text/plain": "foo"}]

    def fake_super_repr(self, **kwargs):
        return [dict(base_result[0])]

    monkeypatch.setattr(m.anywidget.AnyWidget, "_repr_mimebundle_", fake_super_repr)

    widget = CheckboxWidget()
    data = widget._repr_mimebundle_()

    assert data == base_result
