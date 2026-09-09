import math

import pytest

import mercury as mr
import mercury.teletype as teletype_module
from mercury.manager import MERCURY_MIMETYPE, WidgetsManager
from mercury.teletype import Teletype, TeletypeWidget


@pytest.fixture(autouse=True)
def clear_widget_manager():
    WidgetsManager.widgets.clear()
    yield
    WidgetsManager.widgets.clear()


def test_teletype_is_exported_from_public_api():
    assert mr.Teletype is Teletype


def test_factory_displays_and_returns_widget(monkeypatch):
    displayed = []
    monkeypatch.setattr(
        teletype_module, "display", lambda widget: displayed.append(widget)
    )

    widget = Teletype(
        "Loading...\nDone.",
        speed=20,
        cursor=False,
        auto_scroll=False,
        position="bottom",
    )

    assert isinstance(widget, TeletypeWidget)
    assert displayed == [widget]
    assert widget.text == "Loading...\nDone."
    assert widget.speed == 20
    assert widget.cursor is False
    assert widget.auto_scroll is False
    assert widget.position == "bottom"


@pytest.mark.parametrize("text", [None, 42, [], object()])
def test_text_must_be_a_string(text):
    with pytest.raises(TypeError, match="text must be a string"):
        Teletype(text)


@pytest.mark.parametrize("speed", [None, "30", True, []])
def test_speed_must_be_a_number(speed):
    with pytest.raises(TypeError, match="speed must be a finite non-negative number"):
        Teletype("hello", speed=speed)


@pytest.mark.parametrize("speed", [-1, math.inf, -math.inf, math.nan])
def test_speed_must_be_finite_and_non_negative(speed):
    with pytest.raises(ValueError, match="speed must be a finite non-negative number"):
        Teletype("hello", speed=speed)


@pytest.mark.parametrize(
    ("name", "value"),
    [("cursor", "yes"), ("auto_scroll", 1)],
)
def test_boolean_options_are_validated(name, value):
    with pytest.raises(TypeError, match=f"{name} must be a boolean"):
        Teletype("hello", **{name: value})


def test_append_set_clear_and_assignment(monkeypatch):
    monkeypatch.setattr(teletype_module, "display", lambda widget: None)
    widget = Teletype("Loading")

    assert widget.append("...") is None
    assert widget.text == "Loading..."

    assert widget.set("Done") is None
    assert widget.text == "Done"

    widget.text = "Ready"
    assert widget.text == "Ready"

    assert widget.clear() is None
    assert widget.text == ""


def test_update_methods_require_strings(monkeypatch):
    monkeypatch.setattr(teletype_module, "display", lambda widget: None)
    widget = Teletype("")

    for method in (widget.append, widget.set):
        with pytest.raises(TypeError, match="text must be a string"):
            method(42)

    with pytest.raises(teletype_module.traitlets.TraitError):
        widget.text = 42
    with pytest.raises(teletype_module.traitlets.TraitError):
        widget.text = None


def test_speed_assignment_is_validated(monkeypatch):
    monkeypatch.setattr(teletype_module, "display", lambda widget: None)
    widget = Teletype("hello")

    widget.speed = 0
    assert widget.speed == 0

    with pytest.raises(ValueError, match="finite non-negative"):
        widget.speed = -1


def test_stable_key_reuses_and_reconfigures_widget(monkeypatch):
    displayed = []
    monkeypatch.setattr(
        teletype_module, "display", lambda widget: displayed.append(widget)
    )

    first = Teletype("Loading", key="agent-log")
    second = Teletype(
        "Loading...",
        speed=12,
        cursor=False,
        auto_scroll=False,
        position="sidebar",
        key="agent-log",
    )

    assert second is first
    assert second.text == "Loading..."
    assert second.speed == 12
    assert second.cursor is False
    assert second.auto_scroll is False
    assert second.position == "sidebar"
    assert displayed == [first, first]


def test_repr_mimebundle_adds_mercury_metadata(monkeypatch):
    widget = TeletypeWidget(text="hello", position="sidebar")

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
        teletype_module.anywidget.AnyWidget,
        "_repr_mimebundle_",
        fake_super_repr,
    )

    data, _ = widget._repr_mimebundle_()

    assert data[MERCURY_MIMETYPE] == {
        "widget": "TeletypeWidget",
        "model_id": widget.model_id,
        "position": "sidebar",
    }
    assert "text/plain" not in data


def test_frontend_queues_suffixes_and_restarts_replacements():
    esm = TeletypeWidget._esm
    assert "next === target" in esm
    assert "next.startsWith(previousTarget)" in esm
    assert "previousParts[sharedParts] === parts[sharedParts]" in esm
    assert "announce(next.slice(previousTarget.length))" in esm
    assert "revealed = 0" in esm
    assert 'model.on("change:text", drawText)' in esm
    assert "window.requestAnimationFrame(tick)" in esm
    assert "window.cancelAnimationFrame(frame)" in esm
    assert "output.appendData(text)" in esm
    assert 'granularity: "grapheme"' in esm
    assert "Array.from(text)" in esm
    assert "textContent" in esm
    assert "innerHTML" not in esm


def test_frontend_handles_scrolling_cursor_motion_and_accessibility():
    esm = TeletypeWidget._esm
    css = TeletypeWidget._css
    assert 'model.get("auto_scroll") !== false && pinned' in esm
    assert "isNearBottom(container)" in esm
    assert 'announcements.setAttribute("role", "log")' in esm
    assert 'announcements.setAttribute("aria-live", "polite")' in esm
    assert 'visual.setAttribute("aria-hidden", "true")' in esm
    assert 'model.get("cursor") === false' in esm
    assert "prefers-reduced-motion: reduce" in esm
    assert "prefers-reduced-motion: reduce" in css
    assert "mljar-teletype-cursor" in css


def test_styles_use_runtime_mercury_theme_variables():
    for variable in (
        "--mercury-font-size",
        "--mercury-text-color",
        "--mercury-panel-bg",
        "--mercury-card-background-color",
        "--mercury-border-color",
        "--mercury-border-radius",
        "--mercury-primary-color",
        "--mercury-accent-color",
    ):
        assert f"var({variable}" in TeletypeWidget._css


def test_plain_text_preserves_whitespace_and_remains_copyable():
    css = TeletypeWidget._css
    assert "white-space: pre-wrap" in css
    assert "overflow-wrap: anywhere" in css
    assert "user-select: none" in css
