from types import SimpleNamespace

import pytest
from tornado.web import HTTPError

from mercury_app.execution.manifest import NotebookExecutionManifest
from mercury_app.execution.registry import ExecutionRegistry


def manifest():
    return NotebookExecutionManifest.from_notebook(
        "app.ipynb",
        {"cells": [{"id": "safe", "cell_type": "code", "source": "print('safe')"}]},
    )


def test_registry_isolates_sessions_and_kernels_by_browser_owner():
    registry = ExecutionRegistry()
    registry.register(
        owner="browser-a",
        session_id="session-a",
        kernel_id="kernel-a",
        manifest=manifest(),
    )

    assert registry.session_for_owner("session-a", "browser-a").kernel_id == "kernel-a"
    assert registry.kernel_for_owner("kernel-a", "browser-a").session_id == "session-a"
    with pytest.raises(HTTPError) as session_error:
        registry.session_for_owner("session-a", "browser-b")
    with pytest.raises(HTTPError) as kernel_error:
        registry.kernel_for_owner("kernel-a", "browser-b")
    assert session_error.value.status_code == 404
    assert kernel_error.value.status_code == 404


def test_registry_enforces_capacity_and_unregisters_kernel():
    registry = ExecutionRegistry(max_sessions_per_owner=1, max_sessions=2)
    registry.register(
        owner="browser-a",
        session_id="session-a",
        kernel_id="kernel-a",
        manifest=manifest(),
    )
    with pytest.raises(HTTPError) as exc_info:
        registry.register(
            owner="browser-a",
            session_id="session-b",
            kernel_id="kernel-b",
            manifest=manifest(),
        )
    assert exc_info.value.status_code == 429

    registry.unregister_session("session-a")
    with pytest.raises(HTTPError):
        registry.kernel_for_owner("kernel-a", "browser-a")


def test_shared_session_can_attach_another_browser_to_same_manifest():
    registry = ExecutionRegistry()
    trusted_manifest = manifest()
    registry.register(
        owner="browser-a",
        session_id="shared-session",
        kernel_id="shared-kernel",
        manifest=trusted_manifest,
    )

    registry.attach_owner("shared-session", "browser-b", trusted_manifest)
    assert registry.kernel_for_owner("shared-kernel", "browser-b").session_id == (
        "shared-session"
    )

    changed_manifest = NotebookExecutionManifest.from_notebook(
        "app.ipynb",
        {"cells": [{"id": "safe", "cell_type": "code", "source": "print('changed')"}]},
    )
    with pytest.raises(HTTPError) as exc_info:
        registry.attach_owner("shared-session", "browser-c", changed_manifest)
    assert exc_info.value.status_code == 409
