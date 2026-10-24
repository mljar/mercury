import re

import pytest
from tornado.httputil import HTTPServerRequest

from mercury_app.block_handler import BLOCKED_PATTERNS, build_block_rules


def is_blocked(path):
    return any(re.fullmatch(pattern, path) for pattern in BLOCKED_PATTERNS)


def test_terminal_api_is_blocked():
    assert is_blocked("/api/terminals")
    assert is_blocked("/api/terminals/1")
    assert is_blocked("/terminals/websocket/1")


@pytest.mark.parametrize("prefix", ["/api/config", "/nbconvert", "/api/nbconvert"])
def test_config_and_conversion_routes_are_blocked(prefix):
    assert is_blocked(prefix)
    assert is_blocked(prefix + "/")
    assert is_blocked(prefix + "/notebook")


@pytest.mark.parametrize("method", ["GET", "HEAD", "PUT", "PATCH", "POST", "DELETE"])
def test_settings_method_guard_preserves_reads_and_matches_literal_base_url(method):
    rules = build_block_rules("/app.v1/", "/custom/settings/")
    for path in ("/lab/api/settings", "/custom/settings"):
        for suffix in ("", "/", "/plugin"):
            request = HTTPServerRequest(method=method, uri="/app.v1" + path + suffix)
            blocked = any(rule.matcher.match(request) is not None for rule in rules)
            assert blocked == (method not in {"GET", "HEAD"})
        other_app = HTTPServerRequest(method=method, uri="/appXv1" + path)
        assert not any(rule.matcher.match(other_app) is not None for rule in rules)


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
