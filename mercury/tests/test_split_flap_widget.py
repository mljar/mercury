import inspect

import pytest

import mercury as mr
import mercury.split_flap as split_flap_module
from mercury.manager import MERCURY_MIMETYPE, WidgetsManager
from mercury.split_flap import SplitFlap, SplitFlapWidget


@pytest.fixture(autouse=True)
def clear_widget_manager():
    WidgetsManager.widgets.clear()
    yield
    WidgetsManager.widgets.clear()


def test_split_flap_is_exported_from_public_api():
    assert mr.SplitFlap is SplitFlap


def test_split_flap_has_no_label_api_or_trait():
    assert "label" not in inspect.signature(SplitFlap).parameters
    assert "label" not in SplitFlapWidget.class_traits()


@pytest.mark.parametrize(
    ("value", "expected"),
    [("12,482", "12,482"), (42, "42"), (3.14, "3.14")],
)
def test_factory_displays_and_normalizes_supported_values(monkeypatch, value, expected):
    displayed = []
    monkeypatch.setattr(
        split_flap_module, "display", lambda widget: displayed.append(widget)
    )

    widget = SplitFlap(value)

    assert isinstance(widget, SplitFlapWidget)
    assert displayed == [widget]
    assert widget.value == expected


@pytest.mark.parametrize("value", [None, [], {}, object()])
def test_value_must_be_text_or_number(value):
    with pytest.raises(TypeError, match="string or number"):
        SplitFlap(value)


def test_animate_must_be_boolean():
    with pytest.raises(TypeError, match="animate must be a boolean"):
        SplitFlap("42", animate="yes")


@pytest.mark.parametrize("size", ["small", "medium", "large"])
def test_size_variants_are_supported(monkeypatch, size):
    monkeypatch.setattr(split_flap_module, "display", lambda widget: None)
    assert SplitFlap("42", size=size).size == size


def test_invalid_size_is_rejected(monkeypatch):
    monkeypatch.setattr(split_flap_module, "display", lambda widget: None)
    with pytest.raises(split_flap_module.traitlets.TraitError):
        SplitFlap("42", size="giant")


def test_set_updates_value_in_place(monkeypatch):
    monkeypatch.setattr(split_flap_module, "display", lambda widget: None)
    widget = SplitFlap("ON TIME")

    assert widget.set("BOARDING") is None
    assert widget.value == "BOARDING"


def test_value_assignment_normalizes_numbers(monkeypatch):
    monkeypatch.setattr(split_flap_module, "display", lambda widget: None)
    widget = SplitFlap("0")

    widget.value = 128430.52

    assert widget.value == "128430.52"


def test_value_assignment_rejects_unsupported_values(monkeypatch):
    monkeypatch.setattr(split_flap_module, "display", lambda widget: None)
    widget = SplitFlap("0")

    with pytest.raises(TypeError, match="string or number"):
        widget.value = []


def test_stable_key_reuses_and_reconfigures_widget(monkeypatch):
    displayed = []
    monkeypatch.setattr(
        split_flap_module, "display", lambda widget: displayed.append(widget)
    )

    first = SplitFlap("42", key="score")
    second = SplitFlap(
        "105",
        size="large",
        animate=False,
        position="bottom",
        key="score",
    )

    assert second is first
    assert second.value == "105"
    assert second.size == "large"
    assert second.animate is False
    assert second.position == "bottom"
    assert displayed == [first, first]


def test_repr_mimebundle_adds_mercury_metadata(monkeypatch):
    widget = SplitFlapWidget(value="42", position="sidebar")

    def fake_super_repr(self, **kwargs):
        return (
            {
                "application/vnd.jupyter.widget-view+json": {"model_id": self.model_id},
                "text/plain": "fallback",
            },
            {},
        )

    monkeypatch.setattr(
        split_flap_module.anywidget.AnyWidget,
        "_repr_mimebundle_",
        fake_super_repr,
    )

    data, _ = widget._repr_mimebundle_()

    assert data[MERCURY_MIMETYPE] == {
        "widget": "SplitFlapWidget",
        "model_id": widget.model_id,
        "position": "sidebar",
    }
    assert "text/plain" not in data


def test_frontend_has_changed_character_animation_and_accessibility():
    assert "nextCharacter !== previousCharacter" in SplitFlapWidget._esm
    assert (
        "animatedTile(previousCharacter, nextCharacter, changeIndex++)"
        in SplitFlapWidget._esm
    )
    assert "Array.from(value)" in SplitFlapWidget._esm
    assert 'String(value).split("\\n")' in SplitFlapWidget._esm
    assert 'row.className = "mljar-split-flap-row"' in SplitFlapWidget._esm
    assert "existingTile?.dataset.character === nextCharacter" in SplitFlapWidget._esm
    assert "existingTile.replaceWith(tile)" in SplitFlapWidget._esm
    assert "if (hasDrawn && !changed) return" in SplitFlapWidget._esm
    assert 'board.setAttribute("aria-live", "polite")' in SplitFlapWidget._esm
    assert "glyph.textContent" in SplitFlapWidget._esm
    assert (
        "animate && hasDrawn && changed && !reducedMotion.matches"
        in SplitFlapWidget._esm
    )
    assert (
        'window.matchMedia("(prefers-reduced-motion: reduce)")' in SplitFlapWidget._esm
    )
    assert "prefers-reduced-motion: reduce" in SplitFlapWidget._css
    assert "rotateX(-90deg)" in SplitFlapWidget._css
    assert "rotateX(90deg)" in SplitFlapWidget._css
    assert "filter: brightness" not in SplitFlapWidget._css


def test_board_has_no_card_or_tile_borders():
    assert "mljar-split-flap-label" not in SplitFlapWidget._esm
    assert "border:" not in SplitFlapWidget._css
    assert "border-top:" not in SplitFlapWidget._css
    assert "border-bottom:" not in SplitFlapWidget._css
    assert ".mljar-split-flap-row" in SplitFlapWidget._css


def test_styles_use_mercury_theme_variables():
    for variable in (
        "--mercury-border-radius",
        "--mercury-primary-color",
    ):
        assert f"var({variable}" in SplitFlapWidget._css
