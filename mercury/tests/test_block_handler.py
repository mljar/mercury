import re

from mercury_app.block_handler import BLOCKED_PATTERNS


def is_blocked(path):
    return any(re.fullmatch(pattern, path) for pattern in BLOCKED_PATTERNS)


def test_terminal_api_is_blocked():
    assert is_blocked("/api/terminals")
    assert is_blocked("/api/terminals/1")


def test_allowed_lab_apis_are_not_blocked():
    assert not is_blocked("/lab/api/settings")
    assert not is_blocked("/lab/api/settings/@jupyterlab/apputils-extension:themes")
    assert not is_blocked("/lab/api/translations")


def test_lab_and_other_sensitive_endpoints_are_blocked():
    assert is_blocked("/lab")
    assert is_blocked("/lab/workspaces/default")
    assert is_blocked("/api/shutdown")
    assert is_blocked("/api/contents")
    assert is_blocked("/api/contents/secrets.env")
    assert is_blocked("/files/private.txt")
