from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .manifest import ManifestError, NotebookExecutionManifest


class ExecutionDenied(ValueError):
    pass


@dataclass(frozen=True)
class ExecutionDecision:
    code: str
    kind: str


def _url_params_action(payload: Mapping[str, Any]) -> str:
    params = payload.get("params")
    if not isinstance(params, Mapping):
        raise ExecutionDenied("url_params.sync requires an object payload")
    serialized = json.dumps(dict(params), ensure_ascii=False, separators=(",", ":"))
    if len(serialized.encode("utf-8")) > 64 * 1024:
        raise ExecutionDenied("URL parameter payload is too large")
    return (
        "import json as _mercury_json\n"
        "from mercury.url_params import set_runtime_url_params as _mercury_set_url_params\n"
        f"_mercury_set_url_params(_mercury_json.loads({serialized!r}))\n"
        "del _mercury_json, _mercury_set_url_params"
    )


def _widgets_clear_action(payload: Mapping[str, Any]) -> str:
    if payload:
        raise ExecutionDenied("widgets.clear does not accept a payload")
    return (
        "try:\n"
        "    from mercury.manager import WidgetsManager as _MercuryWidgetsManager\n"
        "except Exception:\n"
        "    _MercuryWidgetsManager = None\n"
        "if _MercuryWidgetsManager is not None:\n"
        "    _MercuryWidgetsManager.clear()\n"
        "del _MercuryWidgetsManager"
    )


ACTION_BUILDERS = {
    "url_params.sync": _url_params_action,
    "widgets.clear": _widgets_clear_action,
}


def authorize_execute_request(
    metadata: Mapping[str, Any], manifest: NotebookExecutionManifest
) -> ExecutionDecision:
    mercury = metadata.get("mercury")
    if isinstance(mercury, Mapping):
        kind = mercury.get("kind")
        if kind == "cell":
            cell_id = mercury.get("cell_id")
            revision = mercury.get("revision")
            if revision is not None and revision != manifest.revision:
                raise ExecutionDenied("Notebook execution revision is stale")
            if not isinstance(cell_id, str):
                raise ExecutionDenied("Cell execution is missing a cell id")
            try:
                return ExecutionDecision(manifest.source_for(cell_id), "cell")
            except ManifestError as exc:
                raise ExecutionDenied(str(exc)) from exc
        if kind == "action":
            name = mercury.get("name")
            payload = mercury.get("payload", {})
            if not isinstance(name, str) or name not in ACTION_BUILDERS:
                raise ExecutionDenied("Unknown Mercury action")
            if not isinstance(payload, Mapping):
                raise ExecutionDenied("Mercury action payload must be an object")
            return ExecutionDecision(ACTION_BUILDERS[name](payload), "action")
        raise ExecutionDenied("Unknown Mercury execution kind")

    # Compatibility with the existing frontend while the nested metadata rolls out.
    cell_id = metadata.get("cellId")
    if not isinstance(cell_id, str):
        raise ExecutionDenied("Execution is missing Mercury metadata")
    try:
        return ExecutionDecision(manifest.source_for(cell_id), "cell")
    except ManifestError as exc:
        raise ExecutionDenied(str(exc)) from exc
