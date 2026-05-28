import os
from pathlib import Path

import toml


CONFIG_ENV_VAR = "MERCURY_CONFIG_DIR"


def resolve_config_path(config_path: str = "config.toml") -> Path:
    path = Path(config_path)
    if path.is_absolute():
        return path

    config_dir = os.getenv(CONFIG_ENV_VAR)
    if config_dir:
        return Path(config_dir).expanduser() / path

    return Path.cwd() / path


def load_config_file(config_path: str = "config.toml") -> dict:
    resolved = resolve_config_path(config_path)
    if not resolved.exists():
        return {}
    return toml.load(resolved)
