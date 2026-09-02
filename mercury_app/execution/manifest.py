from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping


class ManifestError(ValueError):
    pass


@dataclass(frozen=True)
class NotebookExecutionManifest:
    path: str
    revision: str
    cells: Mapping[str, str]
    cell_count: int

    @classmethod
    def from_notebook(cls, path: str, notebook: Mapping[str, Any]):
        cells: dict[str, str] = {}
        revision_cells: list[dict[str, str]] = []
        raw_cells = notebook.get("cells")
        if not isinstance(raw_cells, list):
            raise ManifestError("Notebook has no valid cells list")

        for cell in raw_cells:
            if not isinstance(cell, Mapping) or cell.get("cell_type") != "code":
                continue
            cell_id = cell.get("id")
            source = cell.get("source", "")
            if isinstance(source, list):
                source = "".join(str(part) for part in source)
            if not isinstance(cell_id, str) or not cell_id:
                raise ManifestError("Every executable cell must have a cell id")
            if not isinstance(source, str):
                raise ManifestError(f"Cell {cell_id!r} has invalid source")
            if cell_id in cells:
                raise ManifestError(f"Duplicate cell id: {cell_id}")
            cells[cell_id] = source
            revision_cells.append({"id": cell_id, "source": source})

        canonical = json.dumps(
            {"path": path, "cells": revision_cells},
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        revision = hashlib.sha256(canonical).hexdigest()
        return cls(
            path=path,
            revision=revision,
            cells=cells,
            cell_count=len(raw_cells),
        )

    def source_for(self, cell_id: str) -> str:
        try:
            return self.cells[cell_id]
        except KeyError as exc:
            raise ManifestError("Cell is not present in the execution manifest") from exc
