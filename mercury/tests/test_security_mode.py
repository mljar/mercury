from types import SimpleNamespace

from mercury_app.security_mode import SecurityMode, detect_standalone_security_mode


def server(token="", password="", legacy_password=""):
    return SimpleNamespace(
        identity_provider=SimpleNamespace(token=token, hashed_password=password),
        password=legacy_password,
    )


def test_no_credentials_selects_public_firewall_mode():
    assert detect_standalone_security_mode(server()) is SecurityMode.PUBLIC_APP


def test_token_or_password_selects_authenticated_firewall_mode():
    assert detect_standalone_security_mode(server(token="secret")) is SecurityMode.AUTHENTICATED_APP
    assert detect_standalone_security_mode(server(password="hash")) is SecurityMode.AUTHENTICATED_APP
