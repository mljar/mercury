from .config import load_theme_config

def load_theme(config_path="config.toml"):
    return load_theme_config(config_path)

THEME = load_theme()
