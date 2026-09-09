import math

import pytest

import mercury as mr
import mercury.vu_meter as vu_meter_module
from mercury.manager import MERCURY_MIMETYPE, WidgetsManager
from mercury.vu_meter import VUMeter, VUMeterWidget


@pytest.fixture(autouse=True)
def clear_widget_manager():
    WidgetsManager.widgets.clear()
    yield
    WidgetsManager.widgets.clear()


def test_vu_meter_is_exported_from_public_api():
    assert mr.VUMeter is VUMeter


def test_factory_displays_and_returns_widget(monkeypatch):
    displayed = []
    monkeypatch.setattr(
        vu_meter_module, "display", lambda widget: displayed.append(widget)
    )

    meter = VUMeter(
        0.82,
        min=0,
        max=1,
        label="MODEL CONFIDENCE",
        zones=[0.5, 0.8],
    )

    assert isinstance(meter, VUMeterWidget)
    assert displayed == [meter]
    assert meter.value == 0.82
    assert meter.min == 0
    assert meter.max == 1
    assert meter.label == "MODEL CONFIDENCE"
    assert meter.zones == [0.5, 0.8]


@pytest.mark.parametrize("value", [None, "73", [], True])
def test_value_must_be_a_number(value):
    with pytest.raises(TypeError, match="value must be a finite number"):
        VUMeter(value)


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_value_must_be_finite(value):
    with pytest.raises(ValueError, match="value must be a finite number"):
        VUMeter(value)


def test_min_must_be_smaller_than_max():
    with pytest.raises(ValueError, match="min must be smaller than max"):
        VUMeter(1, min=1, max=1)


@pytest.mark.parametrize("zones", [0.5, "0.5, 0.8", [0.5], [0.3, 0.6, 0.9]])
def test_zones_must_be_two_item_sequence(zones):
    error = TypeError if not isinstance(zones, list) else ValueError
    with pytest.raises(error, match="zones must"):
        VUMeter(0.5, min=0, max=1, zones=zones)


@pytest.mark.parametrize("zones", [[0.8, 0.5], [0, 0.8], [0.5, 1]])
def test_zones_must_be_ordered_inside_range(zones):
    with pytest.raises(ValueError, match="ascending and strictly inside"):
        VUMeter(0.5, min=0, max=1, zones=zones)


@pytest.mark.parametrize(("value", "expected"), [(-1, 0.0), (101, 100.0)])
def test_out_of_range_value_is_clamped(value, expected, monkeypatch):
    monkeypatch.setattr(vu_meter_module, "display", lambda widget: None)
    with pytest.warns(UserWarning, match="was clamped"):
        meter = VUMeter(value)
    assert meter.value == expected


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("label", 42),
        ("higher_is_better", "yes"),
        ("animate", "yes"),
    ],
)
def test_display_options_are_validated(name, value):
    with pytest.raises(TypeError, match=name):
        VUMeter(50, **{name: value})


@pytest.mark.parametrize("size", ["small", "medium", "large"])
def test_size_variants_are_supported(size, monkeypatch):
    monkeypatch.setattr(vu_meter_module, "display", lambda widget: None)
    assert VUMeter(50, size=size).size == size


def test_invalid_size_is_rejected(monkeypatch):
    monkeypatch.setattr(vu_meter_module, "display", lambda widget: None)
    with pytest.raises(vu_meter_module.traitlets.TraitError):
        VUMeter(50, size="giant")


def test_set_and_assignment_update_value(monkeypatch):
    monkeypatch.setattr(vu_meter_module, "display", lambda widget: None)
    meter = VUMeter(10)

    assert meter.set(42) is None
    assert meter.value == 42

    meter.value = 73
    assert meter.value == 73


def test_direct_assignment_clamps_to_current_range(monkeypatch):
    monkeypatch.setattr(vu_meter_module, "display", lambda widget: None)
    meter = VUMeter(0.5, min=0, max=1)

    with pytest.warns(UserWarning, match="was clamped"):
        meter.value = 2

    assert meter.value == 1


def test_stable_key_reuses_and_reconfigures_widget(monkeypatch):
    displayed = []
    monkeypatch.setattr(
        vu_meter_module, "display", lambda widget: displayed.append(widget)
    )

    first = VUMeter(25, label="LOAD", key="load")
    second = VUMeter(
        0.9,
        min=0,
        max=1,
        label="CONFIDENCE",
        zones=[0.5, 0.8],
        higher_is_better=False,
        size="large",
        animate=False,
        position="bottom",
        key="load",
    )

    assert second is first
    assert second.value == 0.9
    assert second.min == 0
    assert second.max == 1
    assert second.label == "CONFIDENCE"
    assert second.zones == [0.5, 0.8]
    assert second.higher_is_better is False
    assert second.size == "large"
    assert second.animate is False
    assert second.position == "bottom"
    assert displayed == [first, first]


def test_repr_mimebundle_adds_mercury_metadata(monkeypatch):
    widget = VUMeterWidget(value=42, position="sidebar")

    def fake_super_repr(self, **kwargs):
        return (
            {
                "application/vnd.jupyter.widget-view+json": {"model_id": self.model_id},
                "text/plain": "fallback",
            },
            {},
        )

    monkeypatch.setattr(
        vu_meter_module.anywidget.AnyWidget,
        "_repr_mimebundle_",
        fake_super_repr,
    )

    data, _ = widget._repr_mimebundle_()

    assert data[MERCURY_MIMETYPE] == {
        "widget": "VUMeterWidget",
        "model_id": widget.model_id,
        "position": "sidebar",
    }
    assert "text/plain" not in data


def test_frontend_uses_lightweight_svg_animation_and_accessibility():
    esm = VUMeterWidget._esm
    assert "document.createElementNS(SVG_NS, name)" in esm
    assert 'instrument.setAttribute("role", "meter")' in esm
    assert 'instrument.setAttribute("aria-valuemin"' in esm
    assert 'instrument.setAttribute("aria-valuemax"' in esm
    assert 'instrument.setAttribute("aria-valuenow"' in esm
    assert "needle.style.transform = `rotate(${angle}deg)`" in esm
    assert 'model.on("change:value", drawValue)' in esm
    assert "scale.replaceChildren()" in esm
    assert "textContent" in esm
    assert "innerHTML" not in esm
    assert "requestAnimationFrame" in esm
    assert "mljar-vu-meter-value" not in esm
    assert "mljar-vu-meter-value" not in VUMeterWidget._css
    assert "prefers-reduced-motion: reduce" in VUMeterWidget._css


def test_uses_one_indicator_style_container_border():
    css = VUMeterWidget._css
    assert "show_border" not in VUMeterWidget.class_traits()
    assert "with-border" not in css
    assert "padding: 0" in css
    assert "border: 0.5px solid var(--mercury-border-color" in css
    assert "box-shadow: none" in css
    assert "stroke: none" in css


def test_styles_use_runtime_mercury_theme_variables():
    for variable in (
        "--mercury-font-family",
        "--mercury-heading-font-family",
        "--mercury-text-color",
        "--mercury-muted-text-color",
        "--mercury-panel-bg",
        "--mercury-card-background-color",
        "--mercury-border-color",
        "--mercury-border-radius-lg",
        "--mercury-primary-color",
        "--mercury-accent-color",
        "--mercury-success-color",
        "--mercury-warning-color",
        "--mercury-danger-color",
    ):
        assert f"var({variable}" in VUMeterWidget._css
