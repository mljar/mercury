import mercury.button as m
from mercury.button import Button
from mercury.button import ButtonWidget
from mercury.manager import WidgetsManager


def test_button_trait_defaults():
    w = ButtonWidget()
    assert w.disabled is False
    assert w.hidden is False


def test_button_passes_disabled_and_hidden_to_widget(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)
    WidgetsManager.clear()

    widget = Button(
        label="Run",
        disabled=True,
        hidden=True,
    )

    assert widget.disabled is True
    assert widget.hidden is True
