# mercury/tests/test_select_widget.py

import pytest
from traitlets import TraitError

import mercury.select as m
from mercury.select import SelectWidget


# --- SelectWidget value behaviour -------------------------------------------------

def test_selectwidget_default_value_with_non_empty_choices():
    # empty string -> first element
    w = SelectWidget(choices=["a", "b", "c"], value="")
    assert w.value == "a"

    # invalid non-empty value -> first element
    w2 = SelectWidget(choices=["x", "y"], value="z")
    assert w2.value == "x"


def test_selectwidget_value_not_in_choices_reset_to_first():
    w = SelectWidget(choices=["red", "green"], value="blue")
    assert w.value == "red"


def test_selectwidget_value_in_choices_is_preserved():
    w = SelectWidget(choices=["red", "green"], value="green")
    assert w.value == "green"


def test_selectwidget_empty_choices_keeps_default_value():
    w = SelectWidget(choices=[], value="")
    assert w.value == ""


# --- Trait defaults & validation ---------------------------------------------------

def test_selectwidget_trait_defaults():
    w = SelectWidget()
    assert w.label == "Select"
    assert w.disabled is False
    assert w.hidden is False
    assert w.position == "sidebar"


def test_selectwidget_invalid_position_raises_traiterror():
    w = SelectWidget()
    with pytest.raises(TraitError):
        w.position = "top"  # invalid


# --- _repr_mimebundle_ / MERCURY_MIMETYPE integration -----------------------------

def test_repr_mimebundle_adds_mercury_metadata(monkeypatch):
    # Fake base _repr_mimebundle_ from AnyWidget to control the result
    base_result = [
        {"text/plain": "foo", "application/vnd.jupyter.widget-view+json": {}},
        {"something_else": "bar"},
    ]

    def fake_super_repr(self, **kwargs):
        # Return a shallow copy so our widget can mutate it safely
        return [dict(base_result[0]), dict(base_result[1])]

    # Patch AnyWidget._repr_mimebundle_ so SelectWidget.super() uses this
    monkeypatch.setattr(m.anywidget.AnyWidget, "_repr_mimebundle_", fake_super_repr)

    widget = SelectWidget(position="inline")

    data = widget._repr_mimebundle_()

    # We keep the same length
    assert len(data) == 2

    # Mercury metadata is added to the first mimebundle
    assert m.MERCURY_MIMETYPE in data[0]
    metadata = data[0][m.MERCURY_MIMETYPE]

    # widget name and position are correct
    assert metadata["widget"] == type(widget).__qualname__
    assert metadata["position"] == "inline"

    # model_id should be a non-empty string (we don't care about the exact value)
    assert isinstance(metadata["model_id"], str)
    assert metadata["model_id"]

    # text/plain should be removed
    assert "text/plain" not in data[0]


def test_repr_mimebundle_not_modified_when_single_mimetype(monkeypatch):
    base_result = [{"text/plain": "foo"}]

    def fake_super_repr(self, **kwargs):
        return [dict(base_result[0])]

    monkeypatch.setattr(m.anywidget.AnyWidget, "_repr_mimebundle_", fake_super_repr)

    widget = SelectWidget()
    data = widget._repr_mimebundle_()

    # For len(data) == 1, your code shouldn't modify anything
    assert data == base_result
