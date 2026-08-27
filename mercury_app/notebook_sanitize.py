from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Dict


def sanitize_notebook_for_mercury_runtime(notebook: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return a notebook copy stripped of runtime artifacts.

    Mercury notebooks are treated as app source. Widget state, saved outputs, and
    execution counts are runtime artifacts that should not affect app startup.
    """
    sanitized = copy.deepcopy(notebook)

    metadata = sanitized.get("metadata")
    if isinstance(metadata, dict):
        metadata.pop("widgets", None)

    cells = sanitized.get("cells")
    if not isinstance(cells, list):
        return sanitized

    for index, cell in enumerate(cells):
        if not isinstance(cell, dict):
            continue
        if not isinstance(cell.get("id"), str) or not cell.get("id"):
            identity = json.dumps(
                {
                    "index": index,
                    "type": cell.get("cell_type"),
                    "source": cell.get("source", ""),
                },
                sort_keys=True,
                ensure_ascii=False,
            ).encode("utf-8")
            cell["id"] = f"mrc-{hashlib.sha256(identity).hexdigest()[:20]}"
        if cell.get("cell_type") != "code":
            continue
        cell["outputs"] = []
        cell["execution_count"] = None

    return sanitized
