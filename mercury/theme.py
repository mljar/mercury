import toml
from pathlib import Path

def load_theme(config_path="config.toml"):
    config_file = Path(config_path)
    if not config_file.exists():
        return {}
    config = toml.load(config_file)
    return config.get("theme", {})

THEME = load_theme()