from .config import load_config_file

def load_theme(config_path="config.toml"):
    config = load_config_file(config_path)
    return config.get("theme", {})

THEME = load_theme()
