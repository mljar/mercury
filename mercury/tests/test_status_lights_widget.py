import pytest

import mercury as mr
import mercury.status_lights as status_lights_module
from mercury.manager import MERCURY_MIMETYPE, WidgetsManager
from mercury.status_lights import (
    SUPPORTED_STATES,
    StatusLights,
    StatusLightsWidget,
)


@pytest.fixture(autouse=True)
def clear_widget_manager():
    WidgetsManager.widgets.clear()
    yield
    WidgetsManager.widgets.clear()


def test_status_lights_is_exported_from_public_api():
    assert mr.StatusLights is StatusLights


def test_factory_displays_and_returns_widget(monkeypatch):
    displayed = []
    monkeypatch.setattr(
        status_lights_module, "display", lambda widget: displayed.append(widget)
    )

    widget = StatusLights({"Database": "ok", "Worker": "error"})

    assert isinstance(widget, StatusLightsWidget)
    assert displayed == [widget]
    assert widget.statuses == {"Database": "ok", "Worker": "error"}


def test_all_states_and_state_normalization_are_supported(monkeypatch):
    monkeypatch.setattr(status_lights_module, "display", lambda widget: None)

    widget = StatusLights(
        {state.title(): f"  {state.upper()}  " for state in SUPPORTED_STATES}
    )

    assert tuple(widget.statuses.values()) == SUPPORTED_STATES


@pytest.mark.parametrize("statuses", [None, [], "ok", 42])
def test_statuses_must_be_a_mapping(statuses):
    with pytest.raises(TypeError, match="must be a mapping"):
        StatusLights(statuses)


@pytest.mark.parametrize("label", ["", "   ", None, 42])
def test_labels_must_be_non_empty_strings(label):
    with pytest.raises(ValueError, match="labels must be non-empty strings"):
        StatusLights({label: "ok"})


def test_invalid_state_lists_supported_values():
    with pytest.raises(ValueError, match="Supported states: off, ok, warning"):
        StatusLights({"Database": "unknown"})


def test_animation_labels_must_exist():
    with pytest.raises(ValueError, match="'Worker' is missing from statuses"):
        StatusLights({"Database": "ok"}, blink=["Worker"])


def test_lamp_cannot_blink_and_pulse():
    with pytest.raises(ValueError, match="cannot blink and pulse"):
        StatusLights({"Worker": "active"}, blink=["Worker"], pulse=["Worker"])


def test_set_and_update_change_live_status_traits(monkeypatch):
    monkeypatch.setattr(status_lights_module, "display", lambda widget: None)
    widget = StatusLights({"Extract": "active"})

    assert widget.set("Extract", "ok") is None
    assert widget.update({"Transform": "warning", "Load": "ERROR"}) is None

    assert widget.statuses == {
        "Extract": "ok",
        "Transform": "warning",
        "Load": "error",
    }


def test_set_animation_moves_label_between_animation_modes(monkeypatch):
    monkeypatch.setattr(status_lights_module, "display", lambda widget: None)
    widget = StatusLights({"Worker": "active"}, blink=["Worker"])

    assert widget.set_animation("Worker", "pulse") is None
    assert widget.blink == []
    assert widget.pulse == ["Worker"]

    assert widget.set_animation("Worker", None) is None
    assert widget.blink == []
    assert widget.pulse == []


def test_stable_key_reuses_and_reconfigures_widget(monkeypatch):
    displayed = []
    monkeypatch.setattr(
        status_lights_module, "display", lambda widget: displayed.append(widget)
    )

    first = StatusLights({"API": "active"}, key="health")
    second = StatusLights(
        {"API": "ok", "Worker": "warning"},
        pulse=["Worker"],
        orientation="vertical",
        show_title=False,
        show_group_border=False,
        show_item_borders=False,
        key="health",
    )

    assert second is first
    assert second.statuses == {"API": "ok", "Worker": "warning"}
    assert second.pulse == ["Worker"]
    assert second.orientation == "vertical"
    assert second.show_title is False
    assert second.show_group_border is False
    assert second.show_item_borders is False
    assert displayed == [first, first]


@pytest.mark.parametrize("orientation", ["horizontal", "vertical"])
def test_orientation_variants_are_supported(monkeypatch, orientation):
    monkeypatch.setattr(status_lights_module, "display", lambda widget: None)

    widget = StatusLights({"API": "ok"}, orientation=orientation)

    assert widget.orientation == orientation


def test_invalid_orientation_is_rejected(monkeypatch):
    monkeypatch.setattr(status_lights_module, "display", lambda widget: None)

    with pytest.raises(
        status_lights_module.traitlets.TraitError, match="horizontal.*vertical"
    ):
        StatusLights({"API": "ok"}, orientation="diagonal")


@pytest.mark.parametrize(
    "option",
    ["show_title", "show_group_border", "show_item_borders"],
)
def test_display_options_require_booleans(option):
    with pytest.raises(TypeError, match=f"{option} must be a boolean"):
        StatusLights({"API": "ok"}, **{option: "no"})


def test_repr_mimebundle_adds_mercury_metadata(monkeypatch):
    widget = StatusLightsWidget(statuses={"API": "ok"}, position="sidebar")

    def fake_super_repr(self, **kwargs):
        return (
            {
                "application/vnd.jupyter.widget-view+json": {"model_id": self.model_id},
                "text/plain": "fallback",
            },
            {},
        )

    monkeypatch.setattr(
        status_lights_module.anywidget.AnyWidget,
        "_repr_mimebundle_",
        fake_super_repr,
    )

    data, _ = widget._repr_mimebundle_()

    assert data[MERCURY_MIMETYPE] == {
        "widget": "StatusLightsWidget",
        "model_id": widget.model_id,
        "position": "sidebar",
    }
    assert "text/plain" not in data


def test_frontend_uses_safe_text_and_reduced_motion():
    assert "name.textContent = label" in StatusLightsWidget._esm
    assert "stateLabel.textContent = state" in StatusLightsWidget._esm
    assert "prefers-reduced-motion: reduce" in StatusLightsWidget._css
    assert 'orientation === "vertical"' in StatusLightsWidget._esm
    assert "without-group-border" in StatusLightsWidget._esm
    assert "without-item-borders" in StatusLightsWidget._esm
    assert "var(--mercury-success-color" in StatusLightsWidget._css
    assert "var(--mercury-warning-color" in StatusLightsWidget._css
    assert "var(--mercury-danger-color" in StatusLightsWidget._css
    assert "var(--mercury-primary-color" in StatusLightsWidget._css
