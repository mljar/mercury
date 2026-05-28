from pathlib import Path

from mercury.config import load_config_file, resolve_config_path


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
