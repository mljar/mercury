"""Publishing tests never contact the real platform or open a browser."""

import io
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from mercury_app import __main__, publish as pub
from mercury_app import platform_client as platform


class Question:
    def __init__(self, value):
        self.value = value

    def ask(self):
        return self.value


class UI:
    def __init__(self, answers):
        self.answers = iter(answers)
        self.questions = []

    def prompt(self, *args, **kwargs):
        self.questions.append((args, kwargs))
        return Question(next(self.answers))

    text = confirm = checkbox = prompt

    @staticmethod
    def Choice(title, **kwargs):
        return {"title": title, **kwargs}


@pytest.fixture
def project(tmp_path, monkeypatch):
    (tmp_path / "app.ipynb").write_text('{"cells": []}')
    (tmp_path / "requirements.txt").write_text("mercury\npandas\n")
    (tmp_path / "data").mkdir()
    (tmp_path / "data/sales.csv").write_text("sales\n123\n")
    monkeypatch.delenv("MLJAR_PLATFORM_BASE_URL", raising=False)
    monkeypatch.delenv("MLJAR_PLATFORM_DEFAULT_DOMAIN", raising=False)
    auth = Mock(return_value="secret-test-token")
    monkeypatch.setattr(pub, "authenticate", auth)
    client = Mock()
    client.create_site.return_value = {
        "id": 123,
        "full_domain": "sales.ismvp.org",
        "is_public": True,
    }
    client.list_sites.return_value = [client.create_site.return_value]
    client.upload.side_effect = lambda site, name, stream, size: stream.read()
    monkeypatch.setattr(pub, "PlatformClient", Mock(return_value=client))
    return tmp_path, client, auth


def first_ui(confirm=True):
    return UI(
        ["Sales", "sales", ["app.ipynb", "requirements.txt", "data/sales.csv"], confirm]
    )


def test_create_then_update_remembers_site_and_files(project):
    root, client, auth = project
    pub.publish(root, first_ui())
    state = pub.load_state(root)
    assert state["site_id"] == 123
    assert state["app_url"] == "https://sales.ismvp.org"
    assert len(state["uploaded_files"]) == 3
    assert state["uploaded_files"]["data/sales.csv"]["size"] == 10
    assert "pending_upload" not in state
    assert "secret-test-token" not in (root / pub.STATE_FILE).read_text()
    assert client.upload.call_args_list[-1].args[1] == "data/sales.csv"
    previous = state["last_successful_publish"]
    ui = UI([True, ["app.ipynb"], True])
    pub.publish(root, ui)
    assert client.create_site.call_count == 1
    assert auth.call_count == 2
    assert pub.load_state(root)["files"] == ["app.ipynb"]
    assert pub.load_state(root)["last_successful_publish"] >= previous
    choices = ui.questions[1][1]["choices"]
    assert all(choice["checked"] for choice in choices)


def test_failed_upload_keeps_id_and_retry_updates(project):
    root, client, _ = project
    client.upload.side_effect = platform.PublishError("Network interrupted")
    with pytest.raises(platform.PublishError, match="app.ipynb"):
        pub.publish(root, first_ui())
    state = pub.load_state(root)
    assert state["site_id"] == 123
    assert "last_successful_publish" not in state
    assert len(state["pending_upload"]) == 3
    client.upload.side_effect = None
    pub.publish(root, UI([True, ["app.ipynb"], True]))
    assert client.create_site.call_count == 1
    assert "pending_upload" not in pub.load_state(root)


def test_failed_update_preserves_last_success(project):
    root, client, _ = project
    pub.publish(root, first_ui())
    old = pub.load_state(root)
    client.upload.side_effect = platform.PublishError("Network interrupted")
    with pytest.raises(platform.PublishError):
        pub.publish(root, UI([True, ["app.ipynb"], True]))
    state = pub.load_state(root)
    assert state["uploaded_files"] == old["uploaded_files"]
    assert state["last_successful_publish"] == old["last_successful_publish"]


def test_missing_remote_site_does_not_recreate(project):
    root, client, _ = project
    pub.publish(root, first_ui())
    client.list_sites.return_value = []
    with pytest.raises(platform.PublishError, match="missing or inaccessible"):
        pub.publish(root, UI([]))
    assert client.create_site.call_count == 1


def test_cancel_before_upload_does_not_create_website(project):
    root, client, _ = project
    with pytest.raises(pub.Cancelled):
        pub.publish(root, first_ui(False))
    client.create_site.assert_not_called()
    client.upload.assert_not_called()
    assert not (root / pub.STATE_FILE).exists()


def test_subdomain_conflict_reprompts(project):
    root, client, _ = project
    client.create_site.side_effect = [
        platform.ApiError(400, {"subdomain": ["Already taken"]}),
        {"id": 124, "full_domain": "other.ismvp.org"},
    ]
    pub.publish(root, UI(["Sales", "sales", ["app.ipynb"], True, "other", True]))
    assert client.create_site.call_count == 2
    assert pub.load_state(root)["app_url"] == "https://other.ismvp.org"


def test_account_error_does_not_loop_on_slug(project):
    root, client, _ = project
    client.create_site.side_effect = platform.ApiError(403, {"detail": "Account limit"})
    with pytest.raises(platform.ApiError):
        pub.publish(root, first_ui())
    assert client.create_site.call_count == 1


def test_picker_excludes_credentials_caches_and_symlinks(project):
    root, _, _ = project
    for name in [".env", "credentials.json", "secret.key", "config.env", "id_rsa"]:
        (root / name).touch()
    for name in ["venv", ".git", "node_modules", "custom-env"]:
        (root / name).mkdir()
        (root / name / "pyvenv.cfg").touch()
        (root / name / "private.txt").touch()
    (root / "link.csv").symlink_to(root / "data/sales.csv")
    assert pub.candidates(root) == ["app.ipynb", "data/sales.csv", "requirements.txt"]
    with pytest.raises(platform.PublishError, match="Symbolic"):
        pub.checked_path(root, "link.csv")


@pytest.mark.parametrize(
    "name",
    ["../secret", "/etc/passwd", "data/../../x", ".env", "data\\x", "data//x", "a\nx"],
)
def test_unsafe_paths_rejected(tmp_path, name):
    with pytest.raises(platform.PublishError):
        pub.checked_path(tmp_path, name)


def test_corrupt_state_does_not_create_new_deployment(project):
    root, client, auth = project
    (root / pub.STATE_FILE).write_text("not json")
    with pytest.raises(platform.PublishError, match="Cannot read"):
        pub.publish(root, first_ui())
    auth.assert_not_called()
    client.create_site.assert_not_called()


def test_state_symlink_rejected(tmp_path):
    target = tmp_path / "target.json"
    target.write_text("{}")
    (tmp_path / pub.STATE_FILE).symlink_to(target)
    with pytest.raises(platform.PublishError, match="symbolic"):
        pub.load_state(tmp_path)


def test_lock_and_cleanup(tmp_path):
    with pub.publish_lock(tmp_path):
        with pytest.raises(platform.PublishError, match="Another publish"):
            with pub.publish_lock(tmp_path):
                pass
    assert not (tmp_path / pub.LOCK_FILE).exists()


def test_file_snapshot_is_stable(project):
    root, client, _ = project

    def upload(site, name, stream, size):
        (root / name).write_text("changed during upload")
        assert len(stream.read()) == size

    client.upload.side_effect = upload
    pub.publish(root, first_ui())
    assert pub.load_state(root)["uploaded_files"]["data/sales.csv"]["size"] == 10


def test_cli_dispatch_does_not_start_server(monkeypatch):
    entry = Mock(return_value=0)
    monkeypatch.setattr(pub, "main", entry)
    # Other CLI tests reload mercury_app modules to test configuration isolation.
    monkeypatch.setitem(pub.sys.modules, "mercury_app.publish", pub)
    assert __main__.main(["mercury", "publish", "--working-dir", "project"]) == 0
    entry.assert_called_once_with(["--working-dir", "project"])


def test_cli_help_does_not_authenticate(monkeypatch, capsys):
    auth = Mock()
    monkeypatch.setattr(pub, "authenticate", auth)
    with pytest.raises(SystemExit) as exc:
        pub.main(["--help"])
    assert exc.value.code == 0
    assert "--working-dir" in capsys.readouterr().out
    auth.assert_not_called()


def test_cli_requires_terminal(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(pub.sys.stdin, "isatty", lambda: False)
    assert pub.main(["--working-dir", str(tmp_path)]) == 1
    assert "interactive terminal" in capsys.readouterr().err


def test_login_protocol_and_no_browser(monkeypatch, capsys):
    client = Mock()
    client.base_url = pub.PLATFORM_URL
    client.request.side_effect = [
        {"session_id": "session", "poll_token": "poll-secret"},
        {"status": "completed"},
        {"token": "bearer-secret"},
    ]
    monkeypatch.setattr(platform, "PlatformClient", Mock(return_value=client))
    assert (
        platform.authenticate(pub.PLATFORM_URL, open_browser=False) == "bearer-secret"
    )
    output = capsys.readouterr().out
    assert "desktop-login?session_id=session" in output
    assert "poll-secret" not in output and "bearer-secret" not in output
    assert client.request.call_args.args[1] == "/api/app/auth/session/exchange"


@pytest.mark.parametrize("status", ["expired", "consumed", "denied"])
def test_expired_login(monkeypatch, status):
    client = Mock(base_url=pub.PLATFORM_URL)
    client.request.side_effect = [
        {"session_id": "s", "poll_token": "p"},
        {"status": status},
    ]
    monkeypatch.setattr(platform, "PlatformClient", Mock(return_value=client))
    with pytest.raises(platform.PublishError, match="expired or was declined"):
        platform.authenticate(pub.PLATFORM_URL, open_browser=False)


def test_login_timeout(monkeypatch):
    client = Mock(base_url=pub.PLATFORM_URL)
    client.request.return_value = {"session_id": "s", "poll_token": "p"}
    monkeypatch.setattr(platform, "PlatformClient", Mock(return_value=client))
    monkeypatch.setattr(platform.time, "monotonic", Mock(side_effect=[0, 301]))
    with pytest.raises(platform.PublishError, match="Timed out"):
        platform.authenticate(pub.PLATFORM_URL, open_browser=False)


def test_upload_streams_and_never_sends_auth_to_storage(monkeypatch):
    client = platform.PlatformClient(pub.PLATFORM_URL, "bearer-secret")
    client.request = Mock(
        side_effect=[{"url": "https://storage.example/file?signature=secret"}, None]
    )
    connection = Mock()
    connection.getresponse.return_value.status = 200
    monkeypatch.setattr(
        platform.http.client, "HTTPSConnection", Mock(return_value=connection)
    )
    source = io.BytesIO(b"abc")
    client.upload(123, "data/a b.csv", source, 3)
    assert "data%2Fa%20b.csv" in client.request.call_args_list[0].args[1]
    connection.request.assert_called_once_with(
        "PUT", "/file?signature=secret", body=source, headers={"Content-Length": "3"}
    )
    assert client.request.call_args.args[1] == "/api/file-uploaded"
    connection.close.assert_called_once()


def test_storage_failure_does_not_register_file(monkeypatch):
    client = platform.PlatformClient(pub.PLATFORM_URL)
    client.request = Mock(
        return_value={"url": "https://storage.example/file?secret=token"}
    )
    connection = Mock()
    connection.getresponse.return_value.status = 403
    monkeypatch.setattr(
        platform.http.client, "HTTPSConnection", Mock(return_value=connection)
    )
    with pytest.raises(platform.PublishError, match="HTTP 403") as exc:
        client.upload(1, "app.ipynb", io.BytesIO(), 0)
    assert "token" not in str(exc.value)
    assert client.request.call_count == 1


@pytest.mark.parametrize(
    "url",
    [
        "http://platform.example",
        "https://user:password@platform.example",
        "https://platform.example/path",
        "https://platform.example?token=secret",
    ],
)
def test_invalid_platform_origin_rejected(url):
    with pytest.raises(platform.PublishError):
        platform.PlatformClient(url)


def test_paginated_sites():
    client = platform.PlatformClient(pub.PLATFORM_URL)
    client.request = Mock(
        side_effect=[
            {"results": [{"id": 1}], "next": pub.PLATFORM_URL + "/api/sites/?page=2"},
            {"results": [{"id": 2}], "next": None},
        ]
    )
    assert client.list_sites() == [{"id": 1}, {"id": 2}]
    client.request.assert_called_with("GET", "/api/sites/?page=2")


def test_site_pagination_rejects_external_origin():
    client = platform.PlatformClient(pub.PLATFORM_URL, "secret")
    client.request = Mock(
        return_value={"results": [], "next": "https://other.example/api/sites/"}
    )
    with pytest.raises(platform.PublishError, match="page URL"):
        client.list_sites()
    assert client.request.call_count == 1


def test_real_questionary_checkbox(project):
    import questionary
    from prompt_toolkit.input import create_pipe_input
    from prompt_toolkit.output import DummyOutput

    root, _, _ = project
    with create_pipe_input() as pipe:
        # Default notebook/config selection should be valid on Enter.
        pipe.send_text("\r")

        class TerminalUI:
            Choice = questionary.Choice

            @staticmethod
            def checkbox(*args, **kwargs):
                return questionary.checkbox(
                    *args, **kwargs, input=pipe, output=DummyOutput()
                )

        assert pub.file_picker(TerminalUI, root, {}) == [
            "app.ipynb",
            "requirements.txt",
        ]
