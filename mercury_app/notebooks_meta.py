import json
import os
from typing import Any, Dict, List, Optional, Tuple

# ipynb "mercury" metadata keys -> API field names
MERCURY_THUMBNAIL_KEYS: Dict[str, str] = {
    "thumbnail_bg": "thumbnail_bg",
    "thumbnail_text": "thumbnail_text",
    "thumbnail_text_color": "thumbnail_text_color",
    # common flag name mapping; include if your frontend expects it
    "showCode": "show_code",
}

DEFAULT_THUMBNAILS = {
    "thumbnail_bg": "#f8fafc",        # subtle gray
    "thumbnail_text": "📒",           # notebook emoji
    "thumbnail_text_color": "#0f172a" # slate-900
}


def _read_ipynb_metadata(path: str) -> Tuple[Dict[str, Any], Optional[Exception]]:
    """
    Read a .ipynb file and return (data, error) where data contains:
      - title
      - description
      - mercury (raw 'mercury' dict from metadata)
      - extra_fields (mapped thumbnail/flag fields)
    On failure, returns reasonable fallbacks and the exception.
    """
    filename_stem = os.path.splitext(os.path.basename(path))[0]
    data_out: Dict[str, Any] = {
        "title": filename_stem,
        "description": "",
        "mercury": {},
        "extra_fields": {},
    }

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        meta = data.get("metadata", {}) or {}
        mercury = meta.get("mercury", {}) or {}
        data_out["mercury"] = mercury

        # Title with fallbacks
        data_out["title"] = (
            mercury.get("title")
            or meta.get("title")
            or filename_stem
        )

        # Description with fallbacks
        data_out["description"] = (
            mercury.get("description")
            or meta.get("description")
            or ""
        )

        # Collect potential extra fields (thumbnail + flags)
        extra: Dict[str, Any] = {}
        for ipynb_key, api_field in MERCURY_THUMBNAIL_KEYS.items():
            if ipynb_key in mercury:
                extra[api_field] = mercury.get(ipynb_key)

        data_out["extra_fields"] = extra

    except Exception as e:
        return data_out, e

    return data_out, None


def _iter_notebooks(root: str, recursive: bool = False) -> List[str]:
    if not recursive:
        return sorted(
            [
                os.path.join(root, f)
                for f in os.listdir(root)
                if f.lower().endswith(".ipynb") and os.path.isfile(os.path.join(root, f))
            ]
        )
    # recursive
    paths: List[str] = []
    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            if f.lower().endswith(".ipynb"):
                paths.append(os.path.join(dirpath, f))
    return sorted(paths)


def list_notebooks(
    notebooks_dir: str = ".",
    recursive: bool = False,
) -> List[Dict[str, Any]]:
    """
    Scan `notebooks_dir` (default: current directory) for .ipynb files and
    return a list of dicts with:
        - name
        - description
        - rel_path   (POSIX-style, relative to notebooks_dir)
        - extras     (thumbnail fields, flags) – merged with DEFAULT_THUMBNAILS
        - metadata_error (optional str)
    """
    root = os.path.abspath(notebooks_dir or ".")
    files = _iter_notebooks(root, recursive=recursive)

    out: List[Dict[str, Any]] = []
    for full_path in files:
        meta, err = _read_ipynb_metadata(full_path)
        rel_path = os.path.relpath(full_path, start=root).replace(os.sep, "/")

        # Merge optional extras with defaults
        extras = dict(DEFAULT_THUMBNAILS)
        extras.update(meta.get("extra_fields", {}) or {})

        item = {
            "name": meta.get("title") or os.path.basename(full_path),
            "description": meta.get("description") or "",
            "rel_path": rel_path,
            "extras": extras,
        }
        if err is not None:
            item["metadata_error"] = str(err)

        out.append(item)

    return out
