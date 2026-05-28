import os
import sys
import types
import importlib

import pytest

from mercury_app import __main__
from mercury_app.app import get_effective_notebooks_dir


def test_parse_and_inject_keeps_current_behavior_without_working_dir():
    argv, working_dir = __main__._parse_and_inject(["mercury", "app.ipynb"])

    assert argv[0] == "mercury"
    assert "app.ipynb" in argv
    assert working_dir is None
    assert not any(arg.startswith("--ServerApp.root_dir=") for arg in argv)


def test_parse_and_inject_adds_root_dir_and_strips_working_dir(tmp_path):
    workdir = tmp_path / "test1" / "test2"
    workdir.mkdir(parents=True)

    argv, resolved = __main__._parse_and_inject(
        ["mercury", "app.ipynb", "--working-dir", str(workdir)]
    )

    assert resolved == str(workdir.resolve())
    assert "--working-dir" not in argv
    assert str(workdir) not in argv
    assert f"--ServerApp.root_dir={workdir.resolve()}" in argv
    assert "app.ipynb" in argv


def test_parse_and_inject_rejects_missing_working_dir():
    with pytest.raises(ValueError, match="Working directory does not exist"):
        __main__._parse_and_inject(["mercury", "--working-dir", "missing-dir"])


def test_main_changes_directory_before_launch(monkeypatch, tmp_path):
    workdir = tmp_path / "apps"
    workdir.mkdir()
    original_cwd = os.getcwd()
    calls = {}
    original_config_dir = os.environ.get("MERCURY_CONFIG_DIR")

    fake_app_module = types.ModuleType("mercury_app.app")

    def fake_app_main():
        calls["cwd"] = os.getcwd()
        calls["config_dir"] = os.environ.get("MERCURY_CONFIG_DIR")
        calls["argv"] = list(sys.argv)
        return "started"

    fake_app_module.main = fake_app_main
    monkeypatch.setitem(sys.modules, "mercury_app.app", fake_app_module)

    try:
        result = __main__.main(["mercury", "app.ipynb", "--working-dir", str(workdir)])
    finally:
        if original_config_dir is None:
            os.environ.pop("MERCURY_CONFIG_DIR", None)
        else:
            os.environ["MERCURY_CONFIG_DIR"] = original_config_dir
        os.chdir(original_cwd)
        sys.modules.pop("mercury_app.app", None)

    assert result == "started"
    assert calls["cwd"] == str(workdir.resolve())
    assert calls["config_dir"] == str(workdir.resolve())
    assert "app.ipynb" in calls["argv"]
    assert f"--ServerApp.root_dir={workdir.resolve()}" in calls["argv"]


def test_effective_notebooks_dir_prefers_server_root_dir(tmp_path):
    workdir = tmp_path / "apps"
    workdir.mkdir()

    class ServerAppStub:
        root_dir = str(workdir)

    assert get_effective_notebooks_dir(ServerAppStub()) == str(workdir.resolve())


def test_importing_main_does_not_import_app_or_handlers(monkeypatch):
    for mod in list(sys.modules):
        if mod == "mercury_app" or mod.startswith("mercury_app."):
            sys.modules.pop(mod, None)

    importlib.import_module("mercury_app.__main__")

    assert "mercury_app.app" not in sys.modules
    assert "mercury_app.handlers" not in sys.modules
