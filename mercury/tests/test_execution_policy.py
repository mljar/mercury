import ast

import pytest

from mercury_app.execution.manifest import ManifestError, NotebookExecutionManifest
from mercury_app.execution.policy import ExecutionDenied, authorize_execute_request


def manifest():
    return NotebookExecutionManifest.from_notebook(
        "app.ipynb",
        {
            "cells": [
                {"id": "trusted-cell", "cell_type": "code", "source": "print('trusted')"},
                {"id": "markdown", "cell_type": "markdown", "source": "hello"},
            ]
        },
    )


def test_manifest_contains_only_executable_cells():
    result = manifest()
    assert result.source_for("trusted-cell") == "print('trusted')"
    with pytest.raises(ManifestError):
        result.source_for("markdown")


def test_execute_uses_manifest_source_not_browser_source():
    result = authorize_execute_request(
        {"mercury": {"kind": "cell", "cell_id": "trusted-cell"}}, manifest()
    )
    assert result.code == "print('trusted')"


def test_execute_rejects_missing_or_unknown_cell_metadata():
    with pytest.raises(ExecutionDenied):
        authorize_execute_request({}, manifest())
    with pytest.raises(ExecutionDenied):
        authorize_execute_request({"cellId": "missing"}, manifest())


def test_execute_rejects_stale_revision():
    with pytest.raises(ExecutionDenied, match="stale"):
        authorize_execute_request(
            {
                "mercury": {
                    "kind": "cell",
                    "cell_id": "trusted-cell",
                    "revision": "old",
                }
            },
            manifest(),
        )


def test_named_action_builds_server_owned_code_and_escapes_payload():
    attacker_value = "'); __import__('os').system('id'); #"
    result = authorize_execute_request(
        {
            "mercury": {
                "kind": "action",
                "name": "url_params.sync",
                "payload": {"params": {"q": attacker_value}},
            }
        },
        manifest(),
    )
    tree = ast.parse(result.code, "<mercury-action>", "exec")
    assert "json.loads" in result.code
    assert any(
        isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and attacker_value in node.value
        for node in ast.walk(tree)
    )
    assert not any(isinstance(node, ast.Attribute) and node.attr == "system" for node in ast.walk(tree))


def test_unknown_action_is_rejected():
    with pytest.raises(ExecutionDenied, match="Unknown"):
        authorize_execute_request(
            {"mercury": {"kind": "action", "name": "python.run", "payload": {}}},
            manifest(),
        )
