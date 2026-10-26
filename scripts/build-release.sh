#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-python}"
ALLOW_DIRTY="${ALLOW_DIRTY:-0}"
MAX_SDIST_BYTES="${MAX_SDIST_BYTES:-25000000}"

log() {
  printf '\n==> %s\n' "$*"
}

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Missing required command: $1"
}

require_cmd git
require_cmd jlpm
require_cmd tar
require_cmd "$PYTHON_BIN"

VERSION="$("$PYTHON_BIN" - <<'PY'
import json
from pathlib import Path

print(json.loads(Path("package.json").read_text())["version"])
PY
)"

log "Preparing Mercury ${VERSION} release build"

if [[ "$ALLOW_DIRTY" != "1" ]]; then
  tracked_changes="$(git status --short --untracked-files=no)"
  if [[ -n "$tracked_changes" ]]; then
    printf '%s\n' "$tracked_changes" >&2
    die "Tracked working tree changes found. Commit/stash them or run with ALLOW_DIRTY=1."
  fi
fi

"$PYTHON_BIN" -m build --version >/dev/null 2>&1 || {
  die "Python build module is missing. Install it with: $PYTHON_BIN -m pip install build"
}

log "Installing JavaScript dependencies"
jlpm install --immutable

log "Cleaning generated artifacts"
rm -rf dist build ./*.egg-info
jlpm clean:all

log "Building production frontend artifacts"
jlpm build:prod

log "Building Python wheel and sdist"
"$PYTHON_BIN" -m build

SDIST="dist/mercury-${VERSION}.tar.gz"
WHEEL="dist/mercury-${VERSION}-py3-none-any.whl"

[[ -f "$SDIST" ]] || die "Missing sdist: $SDIST"
[[ -f "$WHEEL" ]] || die "Missing wheel: $WHEEL"

log "Validating release artifacts"
"$PYTHON_BIN" - "$VERSION" "$SDIST" "$WHEEL" "$MAX_SDIST_BYTES" <<'PY'
from __future__ import annotations

import re
import sys
import tarfile
import zipfile
from pathlib import Path

version, sdist_path, wheel_path, max_sdist_bytes = sys.argv[1:]
max_sdist_bytes = int(max_sdist_bytes)

blocked_patterns = [
    re.compile(r"(^|/)\.ollama\.env$"),
    re.compile(r"(^|/)\.env$"),
    re.compile(r"(^|/)\.ipynb_checkpoints(/|$)"),
    re.compile(r"\.ipynb$"),
    re.compile(r"\.map$"),
    re.compile(r"(^|/)build_log\.json$"),
]

required_sdist = [
    f"mercury-{version}/mercury_app/static/bundle.js",
    f"mercury-{version}/mercury_app/labextension/package.json",
]

required_wheel_suffixes = [
    "mercury_app/static/bundle.js",
    f"mercury-{version}.data/data/share/jupyter/labextensions/@mljar/mercury-extension/package.json",
]


def blocked(names: list[str]) -> list[str]:
    return [name for name in names if any(p.search(name) for p in blocked_patterns)]


sdist = Path(sdist_path)
if sdist.stat().st_size > max_sdist_bytes:
    raise SystemExit(
        f"{sdist} is too large: {sdist.stat().st_size} bytes > {max_sdist_bytes}. "
        "This usually means debug/source-map artifacts leaked into the sdist."
    )

with tarfile.open(sdist) as tar:
    sdist_names = tar.getnames()

missing = [name for name in required_sdist if name not in sdist_names]
if missing:
    raise SystemExit(f"sdist is missing required files: {missing}")

bad = blocked(sdist_names)
if bad:
    raise SystemExit("sdist contains blocked files:\n" + "\n".join(bad[:80]))

with zipfile.ZipFile(wheel_path) as wheel:
    wheel_names = wheel.namelist()

missing = [
    suffix
    for suffix in required_wheel_suffixes
    if not any(name.endswith(suffix) for name in wheel_names)
]
if missing:
    raise SystemExit(f"wheel is missing required files: {missing}")

bad = blocked(wheel_names)
if bad:
    raise SystemExit("wheel contains blocked files:\n" + "\n".join(bad[:80]))

print("Artifacts OK")
PY

log "Smoke-testing wheel install and widget MIME"
tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT
"$PYTHON_BIN" -m venv "$tmpdir/venv"
"$tmpdir/venv/bin/python" -m pip install --upgrade pip >/dev/null
"$tmpdir/venv/bin/python" -m pip install "$WHEEL" >/dev/null
"$tmpdir/venv/bin/python" -I - "$VERSION" <<'PY'
import sys

expected = sys.argv[1]

import mercury_app._version as v
from mercury.button import ButtonWidget
from mercury.manager import MERCURY_MIMETYPE

assert v.__version__ == expected, (v.__version__, expected)

widget = ButtonWidget(label="Release smoke test")
bundle = widget._repr_mimebundle_()
data = bundle[0] if isinstance(bundle, tuple) else bundle

assert MERCURY_MIMETYPE in data
assert "application/vnd.jupyter.widget-view+json" in data
assert "text/plain" not in data

print(f"Wheel smoke test OK: {v.__version__}")
PY

log "Release artifacts ready"
ls -lh "$SDIST" "$WHEEL"
