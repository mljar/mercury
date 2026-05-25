import mercury.button as button_module
import mercury.checkbox as checkbox_module
import mercury.columns as columns_module
import mercury.expander as expander_module
import mercury.md as md_module
import mercury.multiselect as multiselect_module
import mercury.number as number_module
import mercury.select as select_module
import mercury.slider as slider_module
import mercury.tabs as tabs_module
import mercury.text as text_module
from mercury.button import Button
from mercury.checkbox import CheckBox
from mercury.columns import Columns
from mercury.expander import Expander
from mercury.manager import WidgetsManager
from mercury.md import Markdown
from mercury.multiselect import MultiSelect
from mercury.number import NumberInput
from mercury.render_context import source_cell_context
from mercury.select import Select
from mercury.slider import Slider
from mercury.tabs import Tabs
from mercury.text import TextInput


def _disable_display(monkeypatch):
    monkeypatch.setattr(button_module, "display", lambda *_: None)
    monkeypatch.setattr(checkbox_module, "display", lambda *_: None)
    monkeypatch.setattr(columns_module, "display", lambda *_: None)
    monkeypatch.setattr(expander_module, "display", lambda *_: None)
    monkeypatch.setattr(md_module, "display", lambda *_: None)
    monkeypatch.setattr(multiselect_module, "display", lambda *_: None)
    monkeypatch.setattr(number_module, "display", lambda *_: None)
    monkeypatch.setattr(select_module, "display", lambda *_: None)
    monkeypatch.setattr(slider_module, "display", lambda *_: None)
    monkeypatch.setattr(tabs_module, "display", lambda *_: None)
    monkeypatch.setattr(text_module, "display", lambda *_: None)


def setup_function():
    WidgetsManager.clear()


def teardown_function():
    WidgetsManager.clear()


def test_button_gets_source_cell_metadata_outside_layout(monkeypatch):
    _disable_display(monkeypatch)

    with source_cell_context("cell-plain"):
        btn = Button("run")

    assert btn.source_cell_id == "cell-plain"
    assert btn.cell_id == "cell-plain"
    assert btn.render_slot_id is None
    assert btn.layout_path is None


def test_button_gets_nested_layout_render_metadata(monkeypatch):
    _disable_display(monkeypatch)

    with source_cell_context("cell-nested"):
        tabs = Tabs(labels=["a"])
        with tabs[0]:
            cols = Columns(2)
            with cols[1]:
                exp = Expander("Details")
                with exp:
                    btn = Button("nested")

    assert btn.source_cell_id == "cell-nested"
    assert btn.cell_id == "cell-nested"
    assert btn.render_slot_id is not None
    assert btn.layout_path is not None
    assert btn.layout_path.endswith(btn.render_slot_id)
    assert "tabs:" in btn.layout_path
    assert "columns:" in btn.layout_path
    assert "expander:" in btn.layout_path


def test_checkbox_gets_source_cell_metadata_outside_layout(monkeypatch):
    _disable_display(monkeypatch)

    with source_cell_context("cell-checkbox-plain"):
        checkbox = CheckBox("enabled")

    assert checkbox.source_cell_id == "cell-checkbox-plain"
    assert checkbox.cell_id == "cell-checkbox-plain"
    assert checkbox.render_slot_id is None
    assert checkbox.layout_path is None


def test_checkbox_gets_nested_layout_render_metadata(monkeypatch):
    _disable_display(monkeypatch)

    with source_cell_context("cell-checkbox-nested"):
        tabs = Tabs(labels=["a"])
        with tabs[0]:
            cols = Columns(2)
            with cols[1]:
                exp = Expander("Details")
                with exp:
                    checkbox = CheckBox("nested")

    assert checkbox.source_cell_id == "cell-checkbox-nested"
    assert checkbox.cell_id == "cell-checkbox-nested"
    assert checkbox.render_slot_id is not None
    assert checkbox.layout_path is not None
    assert checkbox.layout_path.endswith(checkbox.render_slot_id)
    assert "tabs:" in checkbox.layout_path
    assert "columns:" in checkbox.layout_path
    assert "expander:" in checkbox.layout_path


def test_slider_gets_source_cell_metadata_outside_layout(monkeypatch):
    _disable_display(monkeypatch)

    with source_cell_context("cell-slider-plain"):
        slider = Slider("rows", value=3)

    assert slider.source_cell_id == "cell-slider-plain"
    assert slider.cell_id == "cell-slider-plain"
    assert slider.render_slot_id is None
    assert slider.layout_path is None


def test_slider_gets_nested_layout_render_metadata(monkeypatch):
    _disable_display(monkeypatch)

    with source_cell_context("cell-slider-nested"):
        tabs = Tabs(labels=["a"])
        with tabs[0]:
            cols = Columns(2)
            with cols[1]:
                exp = Expander("Details")
                with exp:
                    slider = Slider("nested", value=4)

    assert slider.source_cell_id == "cell-slider-nested"
    assert slider.cell_id == "cell-slider-nested"
    assert slider.render_slot_id is not None
    assert slider.layout_path is not None
    assert slider.layout_path.endswith(slider.render_slot_id)
    assert "tabs:" in slider.layout_path
    assert "columns:" in slider.layout_path
    assert "expander:" in slider.layout_path


def test_select_gets_source_cell_metadata_outside_layout(monkeypatch):
    _disable_display(monkeypatch)

    with source_cell_context("cell-select-plain"):
        select = Select("choice", choices=["a", "b"])

    assert select.source_cell_id == "cell-select-plain"
    assert select.cell_id == "cell-select-plain"
    assert select.render_slot_id is None
    assert select.layout_path is None


def test_select_gets_nested_layout_render_metadata(monkeypatch):
    _disable_display(monkeypatch)

    with source_cell_context("cell-select-nested"):
        tabs = Tabs(labels=["a"])
        with tabs[0]:
            cols = Columns(2)
            with cols[1]:
                exp = Expander("Details")
                with exp:
                    select = Select("nested", choices=["a", "b"])

    assert select.source_cell_id == "cell-select-nested"
    assert select.cell_id == "cell-select-nested"
    assert select.render_slot_id is not None
    assert select.layout_path is not None
    assert select.layout_path.endswith(select.render_slot_id)
    assert "tabs:" in select.layout_path
    assert "columns:" in select.layout_path
    assert "expander:" in select.layout_path


def test_multiselect_gets_source_cell_metadata_outside_layout(monkeypatch):
    _disable_display(monkeypatch)

    with source_cell_context("cell-multiselect-plain"):
        multiselect = MultiSelect("choice", choices=["a", "b"])

    assert multiselect.source_cell_id == "cell-multiselect-plain"
    assert multiselect.cell_id == "cell-multiselect-plain"
    assert multiselect.render_slot_id is None
    assert multiselect.layout_path is None


def test_multiselect_gets_nested_layout_render_metadata(monkeypatch):
    _disable_display(monkeypatch)

    with source_cell_context("cell-multiselect-nested"):
        tabs = Tabs(labels=["a"])
        with tabs[0]:
            cols = Columns(2)
            with cols[1]:
                exp = Expander("Details")
                with exp:
                    multiselect = MultiSelect("nested", choices=["a", "b"])

    assert multiselect.source_cell_id == "cell-multiselect-nested"
    assert multiselect.cell_id == "cell-multiselect-nested"
    assert multiselect.render_slot_id is not None
    assert multiselect.layout_path is not None
    assert multiselect.layout_path.endswith(multiselect.render_slot_id)
    assert "tabs:" in multiselect.layout_path
    assert "columns:" in multiselect.layout_path
    assert "expander:" in multiselect.layout_path


def test_markdown_gets_source_cell_metadata_outside_layout(monkeypatch):
    _disable_display(monkeypatch)

    with source_cell_context("cell-markdown-plain"):
        md = Markdown("hello")

    assert md.source_cell_id == "cell-markdown-plain"
    assert md.cell_id == "cell-markdown-plain"
    assert md.render_slot_id is None
    assert md.layout_path is None


def test_markdown_gets_nested_layout_render_metadata(monkeypatch):
    _disable_display(monkeypatch)

    with source_cell_context("cell-markdown-nested"):
        tabs = Tabs(labels=["a"])
        with tabs[0]:
            cols = Columns(2)
            with cols[1]:
                exp = Expander("Details")
                with exp:
                    md = Markdown("nested")

    assert md.source_cell_id == "cell-markdown-nested"
    assert md.cell_id == "cell-markdown-nested"
    assert md.render_slot_id is not None
    assert md.layout_path is not None
    assert md.layout_path.endswith(md.render_slot_id)
    assert "tabs:" in md.layout_path
    assert "columns:" in md.layout_path
    assert "expander:" in md.layout_path


def test_textinput_gets_source_cell_metadata_outside_layout(monkeypatch):
    _disable_display(monkeypatch)

    with source_cell_context("cell-text-plain"):
        text = TextInput("name", value="Jan")

    assert text.source_cell_id == "cell-text-plain"
    assert text.cell_id == "cell-text-plain"
    assert text.render_slot_id is None
    assert text.layout_path is None


def test_textinput_gets_nested_layout_render_metadata(monkeypatch):
    _disable_display(monkeypatch)

    with source_cell_context("cell-text-nested"):
        tabs = Tabs(labels=["a"])
        with tabs[0]:
            cols = Columns(2)
            with cols[1]:
                exp = Expander("Details")
                with exp:
                    text = TextInput("nested", value="Jan")

    assert text.source_cell_id == "cell-text-nested"
    assert text.cell_id == "cell-text-nested"
    assert text.render_slot_id is not None
    assert text.layout_path is not None
    assert text.layout_path.endswith(text.render_slot_id)
    assert "tabs:" in text.layout_path
    assert "columns:" in text.layout_path
    assert "expander:" in text.layout_path


def test_numberinput_gets_source_cell_metadata_outside_layout(monkeypatch):
    _disable_display(monkeypatch)

    with source_cell_context("cell-number-plain"):
        number = NumberInput("rows", value=3)

    assert number.source_cell_id == "cell-number-plain"
    assert number.cell_id == "cell-number-plain"
    assert number.render_slot_id is None
    assert number.layout_path is None


def test_numberinput_gets_nested_layout_render_metadata(monkeypatch):
    _disable_display(monkeypatch)

    with source_cell_context("cell-number-nested"):
        tabs = Tabs(labels=["a"])
        with tabs[0]:
            cols = Columns(2)
            with cols[1]:
                exp = Expander("Details")
                with exp:
                    number = NumberInput("nested", value=4)

    assert number.source_cell_id == "cell-number-nested"
    assert number.cell_id == "cell-number-nested"
    assert number.render_slot_id is not None
    assert number.layout_path is not None
    assert number.layout_path.endswith(number.render_slot_id)
    assert "tabs:" in number.layout_path
    assert "columns:" in number.layout_path
    assert "expander:" in number.layout_path
