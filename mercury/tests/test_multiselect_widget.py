import pytest
from traitlets import TraitError

import mercury.multiselect as m
from mercury.multiselect import MultiSelectWidget
from mercury.multiselect import MultiSelect
from mercury.manager import WidgetsManager
from mercury.url_params import clear_runtime_url_params, set_runtime_url_params


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


def test_multiselect_respects_explicit_initial_value_on_subsequent_calls(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()

    MultiSelect(label="Choose colors", choices=["Red", "Green", "Blue"])
    widget = MultiSelect(
        label="Choose colors",
        choices=["Red", "Green", "Blue"],
        value=["Green"],
    )

    assert widget.value == ["Green"]


def test_multiselect_uses_repeated_url_params_when_valid(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()
    clear_runtime_url_params()
    set_runtime_url_params({"fruits": ["apple", "banana"]})

    widget = MultiSelect(
        label="Choose fruits",
        choices=["apple", "banana", "cherry"],
        value=["cherry"],
        url_key="fruits",
    )

    assert widget.value == ["apple", "banana"]


def test_multiselect_falls_back_to_value_when_url_param_missing(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()
    clear_runtime_url_params()

    widget = MultiSelect(
        label="Choose fruits",
        choices=["apple", "banana", "cherry"],
        value=["cherry"],
        url_key="fruits",
    )

    assert widget.value == ["cherry"]


def test_multiselect_filters_invalid_and_empty_url_values(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()
    clear_runtime_url_params()
    set_runtime_url_params({"fruits": ["", "banana", "orange"]})

    widget = MultiSelect(
        label="Choose fruits",
        choices=["apple", "banana", "cherry"],
        value=["cherry"],
        url_key="fruits",
    )

    assert widget.value == ["banana"]


def test_multiselect_matches_url_params_case_insensitively(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()
    clear_runtime_url_params()
    set_runtime_url_params({"fruits": ["apple", "BANANA"]})

    widget = MultiSelect(
        label="Choose fruits",
        choices=["Apple", "Banana", "Cherry"],
        value=["Cherry"],
        url_key="fruits",
    )

    assert widget.value == ["Apple", "Banana"]


def test_multiselect_deduplicates_url_values_after_case_insensitive_match(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()
    clear_runtime_url_params()
    set_runtime_url_params({"fruits": ["apple", "Apple", "APPLE"]})

    widget = MultiSelect(
        label="Choose fruits",
        choices=["Apple", "Banana", "Cherry"],
        value=["Cherry"],
        url_key="fruits",
    )

    assert widget.value == ["Apple"]


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
