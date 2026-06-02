from pathlib import Path

from mercury.config import (
    build_theme_css_vars,
    build_theme_font_links,
    load_config_file,
    load_theme_config,
    normalize_theme,
    resolve_config_path,
)


def test_resolve_config_path_prefers_mercury_config_dir(monkeypatch, tmp_path):
    config_dir = tmp_path / "apps"
    config_dir.mkdir()
    monkeypatch.setenv("MERCURY_CONFIG_DIR", str(config_dir))

    resolved = resolve_config_path()

    assert resolved == config_dir / "config.toml"


def test_load_config_file_reads_from_mercury_config_dir(monkeypatch, tmp_path):
    config_dir = tmp_path / "apps"
    config_dir.mkdir()
    (config_dir / "config.toml").write_text("[theme]\nfont_size='22px'\n", encoding="utf-8")
    monkeypatch.setenv("MERCURY_CONFIG_DIR", str(config_dir))

    loaded = load_config_file()

    assert loaded["theme"]["font_size"] == "22px"


def test_resolve_config_path_falls_back_to_cwd(monkeypatch, tmp_path):
    monkeypatch.delenv("MERCURY_CONFIG_DIR", raising=False)
    monkeypatch.chdir(tmp_path)

    resolved = resolve_config_path()

    assert resolved == Path(tmp_path) / "config.toml"


def test_normalize_theme_maps_aliases_and_defaults():
    theme = normalize_theme(
        {
            "backgroundColor": "#101010",
            "surfaceColor": "#181818",
            "textColor": "#efefef",
            "primaryColor": "#ff0000",
            "font": "serif",
        }
    )

    assert theme["background_color"] == "#101010"
    assert theme["surface_color"] == "#181818"
    assert theme["text_color"] == "#efefef"
    assert theme["primary_color"] == "#ff0000"
    assert theme["accent_color"] == "#ff0000"
    assert theme["content_background_color"] == "#181818"
    assert "Georgia" in theme["font_family"]


def test_load_theme_config_normalizes_theme(monkeypatch, tmp_path):
    config_dir = tmp_path / "apps"
    config_dir.mkdir()
    (config_dir / "config.toml").write_text(
        "[theme]\nbackgroundColor='#111827'\naccentColor='#2563eb'\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("MERCURY_CONFIG_DIR", str(config_dir))

    loaded = load_theme_config()

    assert loaded["background_color"] == "#111827"
    assert loaded["accent_color"] == "#2563eb"
    assert loaded["focus_border_color"] == "#2563eb"


def test_load_theme_config_preserves_font_url(monkeypatch, tmp_path):
    config_dir = tmp_path / "apps"
    config_dir.mkdir()
    (config_dir / "config.toml").write_text(
        "[theme]\nfont='Inter, sans-serif'\nfont_url='https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap'\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("MERCURY_CONFIG_DIR", str(config_dir))

    loaded = load_theme_config()

    assert loaded["font_url"] == "https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap"


def test_build_theme_css_vars_contains_normalized_variables():
    css_vars = build_theme_css_vars({"backgroundColor": "#111827", "textColor": "#e5e7eb"})

    assert "--mercury-background-color: #111827;" in css_vars
    assert "--mercury-text-color: #e5e7eb;" in css_vars


def test_build_theme_font_links_adds_google_font_preconnects():
    links = build_theme_font_links(
        {"font_url": "https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap"}
    )

    assert 'rel="preconnect" href="https://fonts.googleapis.com"' in links
    assert 'rel="preconnect" href="https://fonts.gstatic.com" crossorigin' in links
    assert 'rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap"' in links


def test_normalize_theme_applies_overrides_block():
    theme = normalize_theme(
        {
            "background_color": "#f8fafc",
            "primary_color": "#2563eb",
            "overrides": {
                "topbar_background_color": "#111827",
                "topbar_text_color": "#f8fafc",
            },
        }
    )

    assert theme["topbar_background_color"] == "#111827"
    assert theme["topbar_text_color"] == "#f8fafc"
