import pytest
from traitlets import TraitError

import mercury.multiselect as m
from mercury.multiselect import MultiSelectWidget


# --- value & choices behaviour ----------------------------------------------------


def test_multiselectwidget_default_value_with_non_empty_choices():
    # No initial value -> should pick first choice
    w = MultiSelectWidget(choices=["a", "b", "c"])
    assert w.value == ["a"]


def test_multiselectwidget_preserves_valid_selected_values():
    # All selected values are valid -> should stay as is
    w = MultiSelectWidget(choices=["apple", "banana", "cherry"], value=["banana", "cherry"])
    assert w.value == ["banana", "cherry"]


def test_multiselectwidget_filters_invalid_values_and_keeps_valid():
    # Mixed valid/invalid -> keep only valid
    w = MultiSelectWidget(choices=["red", "green"], value=["green", "blue"])
    assert w.value == ["green"]


def test_multiselectwidget_all_invalid_values_fall_back_to_first_choice():
    # All invalid -> fall back to [first choice]
    w = MultiSelectWidget(choices=["red", "green"], value=["blue", "yellow"])
    assert w.value == ["red"]


def test_multiselectwidget_empty_choices_keeps_empty_value():
    # No choices -> value should stay empty list
    w = MultiSelectWidget(choices=[], value=["something"])
    assert w.value == []


# --- Trait defaults & validation ---------------------------------------------------


def test_multiselectwidget_trait_defaults():
    w = MultiSelectWidget()
    assert w.label == "Select"
    assert w.placeholder == ""
    assert w.disabled is False
    assert w.hidden is False
    assert w.position == "sidebar"


def test_multiselectwidget_invalid_position_raises_traiterror():
    w = MultiSelectWidget()
    with pytest.raises(TraitError):
        w.position = "top"  # invalid


# --- _repr_mimebundle_ / MERCURY_MIMETYPE integration -----------------------------


def test_multiselect_repr_mimebundle_adds_mercury_metadata(monkeypatch):
    # Fake base _repr_mimebundle_ from AnyWidget to control the result
    base_result = [
        {"text/plain": "foo", "application/vnd.jupyter.widget-view+json": {}},
        {"something_else": "bar"},
    ]

    def fake_super_repr(self, **kwargs):
        # Return shallow copies so later mutation doesn't affect our base_result
        return [dict(base_result[0]), dict(base_result[1])]

    # Patch AnyWidget._repr_mimebundle_ so MultiSelectWidget.super() uses this
    monkeypatch.setattr(m.anywidget.AnyWidget, "_repr_mimebundle_", fake_super_repr)

    widget = MultiSelectWidget(position="inline")

    data = widget._repr_mimebundle_()

    # We keep the same length
    assert len(data) == 2

    # Mercury metadata is added to the first mimebundle
    assert m.MERCURY_MIMETYPE in data[0]
    metadata = data[0][m.MERCURY_MIMETYPE]

    # Widget name and position are correct
    assert metadata["widget"] == type(widget).__qualname__
    assert metadata["position"] == "inline"

    # model_id should be a non-empty string
    assert isinstance(metadata["model_id"], str)
    assert metadata["model_id"]

    # text/plain should be removed
    assert "text/plain" not in data[0]


def test_multiselect_repr_mimebundle_not_modified_when_single_mimetype(monkeypatch):
    base_result = [{"text/plain": "foo"}]

    def fake_super_repr(self, **kwargs):
        return [dict(base_result[0])]

    monkeypatch.setattr(m.anywidget.AnyWidget, "_repr_mimebundle_", fake_super_repr)

    widget = MultiSelectWidget()
    data = widget._repr_mimebundle_()

    # For len(data) == 1, your code shouldn't modify anything
    assert data == base_result
