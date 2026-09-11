import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from jupyter_server.services.kernels.kernelmanager import MappingKernelManager
from jupyter_server.services.sessions.sessionmanager import SessionManager
from tornado.web import HTTPError

from mercury_app.execution.handlers import (
    ExecutionHandlerMixin,
    MercuryMainKernelHandler,
    MercurySessionRootHandler,
    is_missing_resource_error,
    resolve_session_notebook_path,
)
from mercury_app.execution.manifest import NotebookExecutionManifest
from mercury_app.execution.registry import ExecutionRegistry


def undecorated(method):
    while hasattr(method, "__wrapped__"):
        method = method.__wrapped__
    return method


def manifest(path="app.ipynb"):
    return NotebookExecutionManifest.from_notebook(
        path,
        {"cells": [{"id": "safe", "cell_type": "code", "source": "1 + 1"}]},
    )


class HandlerDouble(ExecutionHandlerMixin):
    def __init__(self, registry, *, keep_session=False, coordinator=None):
        self.settings = {
            "mercury_execution_registry": registry,
            "mercury_config": {"keepSession": keep_session},
        }
        if coordinator is not None:
            self.settings["mercury_shared_session_coordinator"] = coordinator
        self.log = Mock()
        self.finished = None
        self.status = None
        self.headers = {}

    def browser_owner(self, *, create=True):
        return "browser-a"

    def finish(self, value=None):
        self.finished = value

    def set_status(self, status):
        self.status = status

    def set_header(self, name, value):
        self.headers[name] = value


def test_browser_style_session_path_resolves_to_shadow_notebook():
    assert resolve_session_notebook_path(
        ".mercury_sessions/browser-id", "app__mercury__12345678.ipynb"
    ) == ".mercury_sessions/app__mercury__12345678.ipynb"


@pytest.mark.parametrize(
    ("path", "name"),
    [
        ("", "app.ipynb"),
        (".mercury_sessions/browser-id", "../app.ipynb"),
        (".mercury_sessions/browser-id", "app.py"),
    ],
)
def test_session_path_rejects_missing_or_unsafe_notebook_names(path, name):
    with pytest.raises(HTTPError) as exc_info:
        resolve_session_notebook_path(path, name)
    assert exc_info.value.status_code == 400


def test_direct_kernel_creation_is_forbidden():
    with pytest.raises(HTTPError) as exc_info:
        asyncio.run(undecorated(MercuryMainKernelHandler.post)(SimpleNamespace()))
    assert exc_info.value.status_code == 403


@pytest.mark.parametrize("exc", [KeyError("missing"), HTTPError(404)])
def test_missing_resource_error_accepts_key_error_and_http_404(exc):
    assert is_missing_resource_error(exc)


@pytest.mark.parametrize("status", [400, 403, 409, 500])
def test_missing_resource_error_rejects_other_http_errors(status):
    assert not is_missing_resource_error(HTTPError(status))


def test_session_listing_discards_http_404_registry_entry():
    registry = ExecutionRegistry()
    registry.register(
        owner="browser-a",
        session_id="stale-session",
        kernel_id="stale-kernel",
        manifest=manifest(),
    )
    coordinator = SimpleNamespace(remove=Mock())
    handler = HandlerDouble(registry, coordinator=coordinator)
    handler.session_manager = SimpleNamespace(
        get_session=AsyncMock(side_effect=HTTPError(404))
    )

    asyncio.run(undecorated(MercurySessionRootHandler.get)(handler))

    assert json.loads(handler.finished) == []
    assert registry.all_sessions() == []
    coordinator.remove.assert_called_once_with("stale-session")


def test_session_listing_recovers_stock_jupyter_culled_kernel_record():
    registry = ExecutionRegistry()
    registry.register(
        owner="browser-a",
        session_id="stale-session",
        kernel_id="missing-kernel",
        manifest=manifest(),
    )
    kernel_manager = MappingKernelManager()
    session_manager = SessionManager(kernel_manager=kernel_manager)
    session_manager.cursor.execute(
        "INSERT INTO session VALUES (?,?,?,?,?)",
        (
            "stale-session",
            "app.ipynb",
            "app.ipynb",
            "notebook",
            "missing-kernel",
        ),
    )
    handler = HandlerDouble(registry)
    handler.session_manager = session_manager

    try:
        asyncio.run(undecorated(MercurySessionRootHandler.get)(handler))
        remaining = session_manager.cursor.execute(
            "SELECT count(*) FROM session WHERE session_id=?", ("stale-session",)
        ).fetchone()[0]
    finally:
        session_manager.close()

    assert json.loads(handler.finished) == []
    assert remaining == 0
    assert registry.all_sessions() == []


def test_kernel_listing_discards_http_404_registry_entry():
    registry = ExecutionRegistry()
    registry.register(
        owner="browser-a",
        session_id="stale-session",
        kernel_id="stale-kernel",
        manifest=manifest(),
    )
    handler = HandlerDouble(registry)
    handler.kernel_manager = SimpleNamespace(
        kernel_model=Mock(side_effect=HTTPError(404))
    )

    asyncio.run(undecorated(MercuryMainKernelHandler.get)(handler))

    assert json.loads(handler.finished) == []
    assert registry.all_sessions() == []


@pytest.mark.parametrize(
    ("method", "manager_name", "operation"),
    [
        (MercurySessionRootHandler.get, "session_manager", "get_session"),
        (MercuryMainKernelHandler.get, "kernel_manager", "kernel_model"),
    ],
)
def test_listing_does_not_swallow_non_404_http_errors(method, manager_name, operation):
    registry = ExecutionRegistry()
    registry.register(
        owner="browser-a",
        session_id="session-a",
        kernel_id="kernel-a",
        manifest=manifest(),
    )
    handler = HandlerDouble(registry)
    failing_operation = AsyncMock(side_effect=HTTPError(500))
    setattr(handler, manager_name, SimpleNamespace(**{operation: failing_operation}))

    with pytest.raises(HTTPError) as exc_info:
        asyncio.run(undecorated(method)(handler))

    assert exc_info.value.status_code == 500
    assert len(registry.all_sessions()) == 1


def test_independent_session_reopens_after_lookup_http_404():
    notebook_path = ".mercury_sessions/app.ipynb"
    registry = ExecutionRegistry()
    registry.register(
        owner="browser-a",
        session_id="stale-session",
        kernel_id="stale-kernel",
        manifest=manifest(notebook_path),
    )
    handler = HandlerDouble(registry)
    handler.base_url = "/"
    handler.get_json_body = Mock(
        return_value={
            "path": ".mercury_sessions/browser-a",
            "name": "app.ipynb",
            "type": "notebook",
            "kernel": {},
        }
    )
    handler.contents_manager = SimpleNamespace(
        get=AsyncMock(
            return_value={
                "type": "notebook",
                "content": {
                    "cells": [{"id": "safe", "cell_type": "code", "source": "1 + 1"}]
                },
            }
        )
    )
    handler.session_manager = SimpleNamespace(
        session_exists=AsyncMock(return_value=True),
        get_session=AsyncMock(side_effect=HTTPError(404)),
        create_session=AsyncMock(
            return_value={
                "id": "new-session",
                "kernel": {"id": "new-kernel"},
                "path": ".mercury_sessions/browser-a",
            }
        ),
    )

    asyncio.run(undecorated(MercurySessionRootHandler.post)(handler))

    assert registry.session_for_owner("new-session", "browser-a").kernel_id == (
        "new-kernel"
    )
    assert handler.status == 201
    assert json.loads(handler.finished)["id"] == "new-session"
