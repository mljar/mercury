import inspect

import pytest

import mercury as mr
import mercury.examples as examples_module
import mercury.number as number_module
import mercury.select as select_module
from mercury.checkbox import CheckboxWidget
from mercury.date import DateInputWidget
from mercury.daterange import DateRangeWidget
from mercury.datetime_input import DateTimeInputWidget
from mercury.examples import Examples, ExamplesWidget
from mercury.manager import MERCURY_MIMETYPE, WidgetsManager
from mercury.multiselect import MultiSelectWidget
from mercury.number import NumberInputWidget
from mercury.select import SelectWidget
from mercury.slider import SliderWidget
from mercury.text import TextInputWidget
from mercury.time import TimeInputWidget


@pytest.fixture(autouse=True)
def clear_widget_manager():
    WidgetsManager.widgets.clear()
    WidgetsManager.input_widgets.clear()
    yield
    WidgetsManager.widgets.clear()
    WidgetsManager.input_widgets.clear()


def register(identifier, widget, *, url_key="", code_uid=None):
    code_uid = code_uid or f"test.{identifier}.{widget.model_id}"
    WidgetsManager.add_widget(code_uid, widget)
    WidgetsManager.register_input(
        code_uid,
        widget,
        key=identifier,
        url_key=url_key,
    )
    return widget


def test_examples_is_exported_and_defaults_to_sidebar():
    assert mr.Examples is Examples
    assert inspect.signature(Examples).parameters["position"].default == "sidebar"


def test_factory_displays_labels_in_mapping_order(monkeypatch):
    displayed = []
    monkeypatch.setattr(
        examples_module, "display", lambda widget: displayed.append(widget)
    )

    widget = Examples(
        {
            "Young customer": {"age": 25},
            "Enterprise customer": {"age": 45},
        }
    )

    assert isinstance(widget, ExamplesWidget)
    assert displayed == [widget]
    assert widget.labels == ["Young customer", "Enterprise customer"]
    assert widget.position == "sidebar"


@pytest.mark.parametrize("examples", [None, {}, [], "example"])
def test_examples_must_be_a_non_empty_mapping(examples):
    with pytest.raises(ValueError, match="non-empty mapping"):
        Examples(examples)


@pytest.mark.parametrize(
    "examples",
    [
        {1: {"age": 25}},
        {"": {"age": 25}},
        {"Customer": 25},
        {"Customer": {1: 25}},
        {"Customer": {"": 25}},
    ],
)
def test_example_names_entries_and_identifiers_are_validated(examples):
    with pytest.raises(TypeError):
        Examples(examples)


def test_stable_key_reuses_and_reconfigures_component(monkeypatch):
    monkeypatch.setattr(examples_module, "display", lambda widget: None)

    first = Examples({"First": {"age": 20}}, key="presets")
    second = Examples(
        {"Second": {"age": 40}},
        position="inline",
        key="presets",
    )

    assert second is first
    assert second.labels == ["Second"]
    assert second.position == "inline"


def test_registry_resolves_key_before_url_key():
    by_key = register("country", TextInputWidget(value="key"))
    by_url = register(
        "different-key",
        TextInputWidget(value="url"),
        url_key="country",
    )

    source, matches = WidgetsManager.resolve_input("country")

    assert source == "key"
    assert [match.widget for match in matches] == [by_key]
    assert by_url not in [match.widget for match in matches]


def test_registry_ignores_stale_widgets():
    widget = register("age", NumberInputWidget(value=30))
    WidgetsManager.widgets.clear()

    assert WidgetsManager.resolve_input("age") == (None, [])
    assert widget is not None


def test_apply_updates_key_and_url_key_targets():
    age = register("age", NumberInputWidget(value=30, min=18, max=100))
    country = register(
        "customer-country",
        SelectWidget(value="France", choices=["France", "Poland", "Germany"]),
        url_key="country",
    )
    widget = ExamplesWidget(
        examples={"Young customer": {"age": 25, "country": "Poland"}}
    )

    changed, messages = widget._apply_example("Young customer")

    assert changed is True
    assert messages == []
    assert age.value == 25
    assert country.value == "Poland"


def test_input_factories_register_searchable_aliases(monkeypatch):
    monkeypatch.setattr(number_module, "display", lambda widget: None)
    monkeypatch.setattr(select_module, "display", lambda widget: None)
    age = mr.NumberInput(label="Age", value=30, key="age")
    country = mr.Select(
        label="Country",
        value="France",
        choices=["France", "Poland"],
        url_key="country",
    )
    examples = ExamplesWidget(
        examples={"Young customer": {"age": 25, "country": "Poland"}}
    )

    changed, messages = examples._apply_example("Young customer")

    assert changed is True
    assert messages == []
    assert age.value == 25
    assert country.value == "Poland"


@pytest.mark.parametrize(
    ("widget", "value", "expected"),
    [
        (CheckboxWidget(value=False), True, True),
        (DateInputWidget(value="2026-01-01"), "2026-02-03", "2026-02-03"),
        (
            DateRangeWidget(value=["2026-01-01", "2026-01-31"]),
            ["2026-02-01", "2026-02-28"],
            ["2026-02-01", "2026-02-28"],
        ),
        (
            DateTimeInputWidget(value="2026-01-01T08:00"),
            "2026-02-03T09:30",
            "2026-02-03 09:30",
        ),
        (
            MultiSelectWidget(value=[], choices=["A", "B", "C"]),
            ["A", "C"],
            ["A", "C"],
        ),
        (NumberInputWidget(value=1, min=0, max=10), 4.5, 4.5),
        (SelectWidget(value="A", choices=["A", "B"]), "B", "B"),
        (SliderWidget(value=1, min=0, max=10), 6, 6),
        (TextInputWidget(value="before"), "after", "after"),
        (TimeInputWidget(value="08:00"), "14:30", "14:30"),
    ],
)
def test_supported_input_values_are_applied(widget, value, expected):
    register("target", widget)
    examples = ExamplesWidget(examples={"Preset": {"target": value}})

    changed, messages = examples._apply_example("Preset")

    assert changed is True
    assert messages == []
    assert widget.value == expected


def test_missing_ambiguous_and_invalid_targets_warn_but_valid_values_apply():
    valid = register("name", TextInputWidget(value="before"))
    register("duplicate", TextInputWidget(value="one"), code_uid="test.duplicate.1")
    register("duplicate", TextInputWidget(value="two"), code_uid="test.duplicate.2")
    country = register(
        "country",
        SelectWidget(value="Poland", choices=["Poland", "Germany"]),
    )
    examples = ExamplesWidget(
        examples={
            "Preset": {
                "name": "after",
                "missing": 1,
                "duplicate": "value",
                "country": "Spain",
            }
        }
    )

    changed, messages = examples._apply_example("Preset")

    assert changed is True
    assert valid.value == "after"
    assert country.value == "Poland"
    assert "Widget not found: missing." in messages
    assert any("Ambiguous key 'duplicate'" in message for message in messages)
    assert any("Invalid value for 'country'" in message for message in messages)


@pytest.mark.parametrize(
    ("widget", "invalid", "message"),
    [
        (NumberInputWidget(value=5, min=0, max=10), 11, "between 0.0 and 10.0"),
        (SliderWidget(value=5, min=0, max=10), 2.5, "invalid value type"),
        (
            MultiSelectWidget(value=[], choices=["A", "B"]),
            ["A", "C"],
            "unknown choices",
        ),
        (
            DateRangeWidget(value=["2026-01-01", "2026-01-31"]),
            ["2026-03-01", "2026-02-01"],
            "start date before",
        ),
        (DateInputWidget(value="2026-01-01"), "not-a-date", "invalid date"),
    ],
)
def test_invalid_values_are_skipped(widget, invalid, message):
    original = widget.value
    register("target", widget)
    examples = ExamplesWidget(examples={"Preset": {"target": invalid}})

    changed, messages = examples._apply_example("Preset")

    assert changed is False
    assert widget.value == original
    assert message in messages[0]


def test_custom_message_applies_then_acknowledges_once(monkeypatch):
    target = register("name", TextInputWidget(value="before"))
    widget = ExamplesWidget(examples={"Preset": {"name": "after"}})
    sent = []
    monkeypatch.setattr(widget, "send", lambda content: sent.append(content))

    widget._handle_example_message(
        widget,
        {"event": "apply_example", "name": "Preset", "request_id": "request-1"},
        [],
    )

    assert target.value == "after"
    assert widget.selected == "Preset"
    assert widget.warning_messages == []
    assert sent == [
        {"event": "example_applied", "request_id": "request-1", "changed": True}
    ]


def test_custom_message_exposes_missing_target_warning(monkeypatch):
    widget = ExamplesWidget(examples={"Preset": {"missing": "value"}})
    sent = []
    monkeypatch.setattr(widget, "send", lambda content: sent.append(content))

    with pytest.warns(UserWarning, match="Widget not found: missing"):
        widget._handle_example_message(
            widget,
            {
                "event": "apply_example",
                "name": "Preset",
                "request_id": "request-1",
            },
            [],
        )

    assert widget.warning_messages == ["Widget not found: missing."]
    assert sent[0]["changed"] is False


def test_repr_mimebundle_adds_mercury_metadata(monkeypatch):
    widget = ExamplesWidget(examples={"Preset": {}}, position="inline")

    def fake_super_repr(self, **kwargs):
        return (
            {
                "application/vnd.jupyter.widget-view+json": {
                    "model_id": self.model_id
                },
                "text/plain": "fallback",
            },
            {},
        )

    monkeypatch.setattr(
        examples_module.anywidget.AnyWidget,
        "_repr_mimebundle_",
        fake_super_repr,
    )

    data, _ = widget._repr_mimebundle_()

    assert data[MERCURY_MIMETYPE] == {
        "widget": "ExamplesWidget",
        "model_id": widget.model_id,
        "position": "inline",
    }
    assert "text/plain" not in data


def test_frontend_uses_apply_acknowledgement_and_one_saved_tick():
    esm = ExamplesWidget._esm
    assert 'model.send({' in esm
    assert 'event: "apply_example"' in esm
    assert 'content?.event !== "example_applied"' in esm
    assert 'model.set("apply_tick"' in esm
    assert esm.count("model.save_changes()") == 1
    assert 'model.on("msg:custom", handleMessage)' in esm
    assert "button.textContent = name" in esm
    assert "innerHTML" not in esm


def test_frontend_is_accessible_and_uses_mercury_theme():
    esm = ExamplesWidget._esm
    css = ExamplesWidget._css
    assert 'heading.textContent = "Examples"' in esm
    assert 'warning.setAttribute("aria-live", "polite")' in esm
    assert 'button.setAttribute("aria-pressed"' in esm
    assert 'root.setAttribute("aria-busy"' in esm
    for variable in (
        "--mercury-font-family",
        "--mercury-heading-font-family",
        "--mercury-font-size",
        "--mercury-text-color",
        "--mercury-widget-background-color",
        "--mercury-card-background-color",
        "--mercury-border-color",
        "--mercury-border-radius",
        "--mercury-primary-color",
        "--mercury-accent-color",
        "--mercury-warning-color",
    ):
        assert f"var({variable}" in css
    assert "border-radius: var(--mercury-border-radius, 8px) !important" in css
