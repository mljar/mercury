import asyncio
from types import SimpleNamespace

import pytest
from tornado.web import HTTPError

from mercury_app.execution.handlers import (
    MercuryMainKernelHandler,
    resolve_session_notebook_path,
)


def undecorated(method):
    while hasattr(method, "__wrapped__"):
        method = method.__wrapped__
    return method


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
