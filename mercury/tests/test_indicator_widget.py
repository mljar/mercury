import mercury.indicator as indicator_module
from mercury.indicator import Indicator


def test_indicator_display_now_false_does_not_display(monkeypatch):
    displayed = []
    monkeypatch.setattr(indicator_module, "display", lambda widget: displayed.append(widget))

    indicator = Indicator(value="123", label="Users", display_now=False)

    assert isinstance(indicator, Indicator)
    assert displayed == []


def test_indicator_display_now_true_displays_once(monkeypatch):
    displayed = []
    monkeypatch.setattr(indicator_module, "display", lambda widget: displayed.append(widget))

    indicator = Indicator(value="123", label="Users", display_now=True)

    assert displayed == [indicator]


def test_indicator_display_method_displays_once(monkeypatch):
    displayed = []
    monkeypatch.setattr(indicator_module, "display", lambda widget: displayed.append(widget))

    indicator = Indicator(value="123", label="Users")
    indicator.display()

    assert displayed == [indicator]


def test_indicator_single_renders_inline_colors():
    html = Indicator(
        value="123",
        label="Users",
        background_color="#ff0000",
        border_color="#00ff00",
        value_color="#0000ff",
        label_color="#999999",
    )._repr_html_()

    assert "background:#ff0000" in html
    assert "border:0.5px solid #00ff00" in html
    assert "style='color:#999999;'" in html
    assert "style='color:#0000ff;'" in html
    assert "Users" in html
    assert "123" in html


def test_indicator_positive_delta_renders_up_badge():
    html = Indicator(value="123", delta=5.4)._repr_html_()

    assert "&#8593;" in html
    assert "5.4%" in html
    assert f"background:{Indicator._DELTA_UP_BG}" in html
    assert f"color:{Indicator._DELTA_UP_FG}" in html


def test_indicator_negative_delta_renders_down_badge():
    html = Indicator(value="123", delta=-1.2)._repr_html_()

    assert "&#8595;" in html
    assert "1.2%" in html
    assert f"background:{Indicator._DELTA_DOWN_BG}" in html
    assert f"color:{Indicator._DELTA_DOWN_FG}" in html


def test_indicator_zero_delta_renders_neutral_badge():
    indicator = Indicator(value="123", delta=0)
    html = indicator._repr_html_()

    assert "0%" in html
    assert "&#8593;" not in html
    assert "&#8595;" not in html
    assert "&#8212;&nbsp;0%" in html
    assert f"background:{indicator._badge_bg}" in html
    assert f"color:{indicator._badge_fg}" in html


def test_indicator_non_numeric_delta_renders_raw_text():
    html = Indicator(value="OK", delta="stable")._repr_html_()

    assert "stable" in html
    assert "&#8593;" not in html
    assert "&#8595;" not in html


def test_indicator_list_renders_row_of_cards():
    html = Indicator(
        [
            Indicator(value="123", label="Users"),
            Indicator(value="98%", label="Accuracy"),
        ]
    )._repr_html_()

    assert "mljar-ind-row" in html
    assert html.count("mljar-ind-card") >= 2
    assert "Users" in html
    assert "Accuracy" in html
