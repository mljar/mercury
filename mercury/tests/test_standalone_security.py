"""Verify route guards against real Jupyter endpoints, including extension mode."""

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import nbformat
import pytest
import requests
import websocket


@pytest.fixture(
    scope="module",
    params=[
        ("public", "/"),
        ("public", "/prefix/"),
        ("token", "/prefix/"),
        ("extension", "/prefix/"),
    ],
    ids=["public-root", "public-prefix", "token-prefix", "jupyterlab-extension"],
)
def server(request, tmp_path_factory):
    mode, base_url = request.param
    root = tmp_path_factory.mktemp("mercury-security")
    repo = Path(__file__).resolve().parents[2]
    for directory in (
        "notebooks",
        "config",
        "data",
        "runtime",
        "settings",
        "workspaces",
        "ipython",
    ):
        (root / directory).mkdir()
    notebook = nbformat.v4.new_notebook(
        cells=[
            nbformat.v4.new_code_cell(
                source="print('SOURCE_CANARY')",
                outputs=[
                    nbformat.v4.new_output(
                        "stream", name="stdout", text="OUTPUT_CANARY"
                    )
                ],
            )
        ],
        metadata={
            "kernelspec": {
                "name": "python3",
                "language": "python",
                "display_name": "Python 3",
            }
        },
    )
    nbformat.write(notebook, root / "notebooks" / "app.ipynb")
    kernel_dir = root / "data" / "kernels" / "security-audit"
    kernel_dir.mkdir(parents=True)
    (kernel_dir / "kernel.json").write_text(
        json.dumps(
            {
                "argv": [
                    sys.executable,
                    "-m",
                    "ipykernel_launcher",
                    "-f",
                    "{connection_file}",
                ],
                "display_name": "Security audit",
                "language": "python",
                "env": {"API_KEY": "KERNEL_SECRET_CANARY"},
                "metadata": {"private": "KERNEL_SECRET_CANARY"},
            }
        )
    )
    (kernel_dir / "private.txt").write_text("KERNEL_SECRET_CANARY")
    # Seed an existing PTY without exposing a creation endpoint or executing shell
    # commands. This catches the gap between terminal REST and WebSocket routes.
    (root / "terminal_fixture.py").write_text(
        "import sys\n"
        "from pathlib import Path\n"
        "from jupyter_server_terminals.terminalmanager import TerminalManager\n"
        "class SeededTerminalManager(TerminalManager):\n"
        "    def __init__(self, *args, **kwargs):\n"
        "        kwargs['shell_command'] = [sys.executable, '-u', '-c', 'import sys; sys.stdin.read()']\n"
        "        super().__init__(*args, **kwargs)\n"
        "        terminal = self.create()\n"
        "        Path(__file__).with_suffix('.ready').write_text(terminal['name'])\n",
        encoding="utf-8",
    )
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(
            ("MERCURY_", "JUPYTER_", "JUPYTERLAB_", "IPYTHON", "GH_", "GITHUB_")
        )
    }
    env.update(
        PYTHONPATH=os.pathsep.join((str(repo), str(root))),
        JUPYTER_CONFIG_DIR=str(root / "config"),
        JUPYTER_CONFIG_PATH=str(root / "config"),
        JUPYTER_DATA_DIR=str(root / "data"),
        JUPYTER_RUNTIME_DIR=str(root / "runtime"),
        JUPYTERLAB_SETTINGS_DIR=str(root / "settings"),
        JUPYTERLAB_WORKSPACES_DIR=str(root / "workspaces"),
        IPYTHONDIR=str(root / "ipython"),
    )
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    token = "security-test-token" if mode in {"token", "extension"} else ""
    cmd = [sys.executable, "-m", "jupyterlab" if mode == "extension" else "mercury_app"]
    cmd += [
        "--ServerApp.ip=127.0.0.1",
        f"--ServerApp.port={port}",
        "--ServerApp.port_retries=0",
        "--ServerApp.open_browser=False",
        "--ServerApp.allow_root=True",
        "--ServerApp.log_level=30",
        f"--ServerApp.base_url={base_url}",
        f"--ServerApp.root_dir={root / 'notebooks'}",
        "--IdentityProvider.hashed_password=",
        "--ServerApp.terminals_enabled=True",
        "--TerminalsExtensionApp.terminal_manager_class=terminal_fixture.SeededTerminalManager",
        "--ServerApp.jpserver_extensions={'jupyterlab':True,'jupyter_server_terminals':True,'mercury_app':True}",
    ]
    if mode == "extension":
        cmd.append(f"--IdentityProvider.token={token}")
    elif token:
        cmd.append(f"--token={token}")
    log_path = root / "server.log"
    with log_path.open("w") as log, requests.Session() as client:
        client.trust_env = False
        url = f"http://127.0.0.1:{port}{base_url.rstrip('/')}"
        process = subprocess.Popen(
            cmd, cwd=root / "notebooks", env=env, stdout=log, stderr=log
        )
        try:
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    pytest.fail(log_path.read_text())
                try:
                    client.get(url + "/api/status", timeout=0.2)
                    break
                except requests.RequestException:
                    time.sleep(0.1)
            else:
                pytest.fail("Server startup timed out:\n" + log_path.read_text())
            assert (root / "terminal_fixture.ready").read_text() == "1"
            # Obtain a real XSRF cookie before supplying credentials, so writes
            # cannot pass these tests just because Jupyter rejected missing XSRF.
            client.get(url + "/login", timeout=10)
            xsrf = next(
                cookie.value for cookie in client.cookies if cookie.name == "_xsrf"
            )
            client.headers["X-XSRFToken"] = xsrf
            if token:
                client.headers["Authorization"] = "token " + token
            yield {
                "client": client,
                "url": url,
                "root": root,
                "extension": mode == "extension",
            }
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def test_config_store_is_blocked_only_in_standalone(server):
    client, url, root = server["client"], server["url"], server["root"]
    endpoint = url + "/api/config/security_test"
    for method in ("PUT", "PATCH"):
        response = client.request(
            method, endpoint, json={"canary": "CONFIG_WRITE_CANARY"}, timeout=10
        )
        expected = (204 if method == "PUT" else 200) if server["extension"] else 403
        assert response.status_code == expected, response.text
    response = client.get(endpoint, timeout=10)
    assert response.status_code == (200 if server["extension"] else 403)
    persisted = root / "config" / "serverconfig" / "security_test.json"
    assert persisted.exists() == server["extension"]


def test_nbconvert_cannot_export_saved_content_in_standalone(server):
    for fmt in ("html", "script"):
        response = server["client"].get(
            server["url"] + f"/nbconvert/{fmt}/app.ipynb", timeout=20
        )
        assert response.status_code == (
            200 if server["extension"] else 403
        ), response.text
        assert ("SOURCE_CANARY" in response.text) == server["extension"]
        if fmt == "html":
            assert ("OUTPUT_CANARY" in response.text) == server["extension"]


def test_existing_terminal_websocket_is_blocked_only_in_standalone(server):
    # A real WebSocket upgrade must be denied before it reaches the seeded PTY.
    # Stream the response so a successful extension-mode upgrade does not wait
    # for the WebSocket to close as though it were an HTTP response body.
    with server["client"].get(
        server["url"] + "/terminals/websocket/1",
        headers={
            "Connection": "Upgrade",
            "Upgrade": "websocket",
            "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
            "Sec-WebSocket-Version": "13",
        },
        stream=True,
        timeout=10,
    ) as response:
        assert response.status_code == (101 if server["extension"] else 403)


def test_settings_remain_readable_but_writes_are_blocked_in_standalone(server):
    endpoint = server["url"] + "/lab/api/settings/@jupyterlab/apputils-extension:themes"
    response = server["client"].get(endpoint, timeout=10)
    assert response.status_code == 200, response.text
    original = response.json()["raw"]
    response = server["client"].put(
        endpoint,
        json={"raw": json.dumps({"theme": "SETTINGS_WRITE_CANARY"})},
        timeout=10,
    )
    assert response.status_code == (204 if server["extension"] else 403), response.text
    response = server["client"].get(endpoint, timeout=10)
    assert response.status_code == 200, response.text
    if server["extension"]:
        assert "SETTINGS_WRITE_CANARY" in response.json()["raw"]
    else:
        assert response.json()["raw"] == original
        assert not list((server["root"] / "settings").rglob("*.jupyterlab-settings"))


def test_app_and_required_read_routes_still_load(server):
    paths = ["/lab/api/translations", "/api/kernelspecs"]
    if not server["extension"]:
        paths += ["/", "/mercury/api/notebooks", "/mercury/app.ipynb"]
    for path in paths:
        response = server["client"].get(server["url"] + path, timeout=10)
        assert response.status_code == 200, (path, response.text)


def test_kernel_specs_do_not_expose_launch_secrets_in_standalone(server):
    for path in ("/api/kernelspecs", "/api/kernelspecs/security-audit"):
        response = server["client"].get(server["url"] + path, timeout=10)
        assert response.status_code == 200, response.text
        assert "Security audit" in response.text
        assert ("KERNEL_SECRET_CANARY" in response.text) == server["extension"]
        if not server["extension"]:
            data = response.json()
            model = data.get("kernelspecs", {}).get("security-audit", data)
            assert model["spec"]["argv"] == []
            assert model["spec"]["env"] == {}
            assert model["resources"] == {}
    for name in ("kernel.json", "private.txt"):
        response = server["client"].get(
            server["url"] + "/kernelspecs/security-audit/" + name, timeout=10
        )
        assert response.status_code == (200 if server["extension"] else 403)
        assert ("KERNEL_SECRET_CANARY" in response.text) == server["extension"]


def test_independent_session_cannot_be_claimed_by_another_browser(server):
    client, url = server["client"], server["url"]
    payload = {
        "path": "app.ipynb",
        "name": "app.ipynb",
        "type": "notebook",
        "kernel": {"name": "python3"},
    }
    first = client.post(url + "/api/sessions", json=payload, timeout=20)
    assert first.status_code == 201, first.text
    session_id = first.json()["id"]
    with requests.Session() as other:
        other.trust_env = False
        other.get(url + "/login", timeout=10)
        other.headers["X-XSRFToken"] = other.cookies.get("_xsrf")
        if "Authorization" in client.headers:
            other.headers["Authorization"] = client.headers["Authorization"]
        response = other.post(url + "/api/sessions", json=payload, timeout=20)
        assert response.status_code == (
            201 if server["extension"] else 404
        ), response.text
        response = other.get(url + "/api/sessions/" + session_id, timeout=10)
        assert response.status_code == (200 if server["extension"] else 404)
    # Reopening from the original browser must still work.
    same = client.post(url + "/api/sessions", json=payload, timeout=20)
    assert same.status_code == 201
    assert same.json()["id"] == session_id


def test_server_events_are_not_shared_with_app_viewers(server):
    client, url = server["client"], server["url"]
    headers = []
    if "Authorization" in client.headers:
        headers.append("Authorization: " + client.headers["Authorization"])
    sock = websocket.create_connection(
        url.replace("http://", "ws://") + "/api/events/subscribe",
        cookie="; ".join(f"{c.name}={c.value}" for c in client.cookies),
        header=headers,
        origin=url.split("/prefix")[0],
        timeout=1,
    )
    try:
        response = client.post(
            url + "/api/events",
            json={
                "schema_id": "https://events.jupyter.org/jupyter_server/contents_service/v1",
                "version": "1",
                "data": {"action": "get", "path": "EVENT_CANARY.ipynb"},
            },
            timeout=10,
        )
        assert response.status_code == (204 if server["extension"] else 403)
        response = client.get(url + "/api/contents/app.ipynb", timeout=10)
        assert response.status_code == 200
        if server["extension"]:
            assert "EVENT_CANARY" in sock.recv()
        else:
            with pytest.raises(websocket.WebSocketTimeoutException):
                sock.recv()
    finally:
        sock.close()
