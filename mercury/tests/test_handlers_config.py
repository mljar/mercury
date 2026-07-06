from mercury_app.handlers import (
    _css_string_literal,
    _normalize_starting_icon,
    load_config,
)


def test_load_config_reads_main_starting_message(monkeypatch, tmp_path):
    config_dir = tmp_path / "apps"
    config_dir.mkdir()
    (config_dir / "config.toml").write_text(
        "[main]\nstarting_message='Loading custom app message'\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("MERCURY_CONFIG_DIR", str(config_dir))

    loaded = load_config()

    assert loaded["main"]["starting_message"] == "Loading custom app message"


def test_load_config_reads_main_starting_icon(monkeypatch, tmp_path):
    config_dir = tmp_path / "apps"
    config_dir.mkdir()
    (config_dir / "config.toml").write_text(
        "[main]\nstarting_icon='spinner'\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("MERCURY_CONFIG_DIR", str(config_dir))

    loaded = load_config()

    assert loaded["main"]["starting_icon"] == "spinner"


def test_css_string_literal_escapes_quotes_and_newlines():
    escaped = _css_string_literal('Loading "Demo"\nPlease wait')

    assert escaped == '"Loading \\"Demo\\"\\nPlease wait"'


def test_normalize_starting_icon_accepts_supported_values():
    assert _normalize_starting_icon("coffee") == "coffee"
    assert _normalize_starting_icon("spinner") == "spinner"
    assert _normalize_starting_icon("none") == "none"


def test_normalize_starting_icon_falls_back_to_coffee():
    assert _normalize_starting_icon("coffee+spinner") == "coffee"
    assert _normalize_starting_icon("invalid") == "coffee"
    assert _normalize_starting_icon(None) == "coffee"
