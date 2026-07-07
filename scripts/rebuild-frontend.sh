#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

log() {
  printf '\n==> %s\n' "$*"
}

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

if command -v jlpm >/dev/null 2>&1; then
  PM="jlpm"
elif command -v yarn >/dev/null 2>&1; then
  PM="yarn"
else
  die "Missing JavaScript package manager: expected jlpm or yarn"
fi

PYTHON_BIN="${PYTHON_BIN:-}"
if [[ -z "$PYTHON_BIN" ]]; then
  if [[ -x "$ROOT/venv/bin/python" ]]; then
    PYTHON_BIN="$ROOT/venv/bin/python"
  else
    PYTHON_BIN="python"
  fi
fi

log "Building Mercury extension TypeScript"
"$PM" workspace @mljar/mercury-extension run build:lib:prod

log "Building Mercury application TypeScript"
"$PM" workspace mercury-application run build:prod

log "Building Mercury labextension artifact"
PATH="$ROOT/venv/bin:$PATH" "$PYTHON_BIN" -m jupyter labextension build packages/lab

log "Cleaning standalone Mercury app static bundle"
"$PM" workspace mercury-app run clean:static

log "Building standalone Mercury app static bundle"
"$PM" workspace mercury-app run build

log "Frontend rebuild complete"
