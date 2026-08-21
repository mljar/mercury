from jupyter_server.auth.identity import PasswordIdentityProvider
from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application

from mercury_app.handlers import (
    MercuryLogoutHandler,
    _normalize_starting_icon,
    _safe_logout_next_url,
    is_logout_available,
    load_config,
)


def test_load_config_reads_main_starting_message(monkeypatch, tmp_path):
    config_dir = tmp_path / "apps"
    config_dir.mkdir()
    (config_dir / "config.toml").write_text(
        "[main]\nstarting_message='Loading custom app message'\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("MERCURY_CONFIG_DIR", str(config_dir))

    loaded = load_config()

    assert loaded["main"]["starting_message"] == "Loading custom app message"


def test_load_config_reads_main_starting_icon(monkeypatch, tmp_path):
    config_dir = tmp_path / "apps"
    config_dir.mkdir()
    (config_dir / "config.toml").write_text(
        "[main]\nstarting_icon='spinner'\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("MERCURY_CONFIG_DIR", str(config_dir))

    loaded = load_config()

    assert loaded["main"]["starting_icon"] == "spinner"


def test_normalize_starting_icon_accepts_supported_values():
    assert _normalize_starting_icon("coffee") == "coffee"
    assert _normalize_starting_icon("spinner") == "spinner"
    assert _normalize_starting_icon("none") == "none"


def test_normalize_starting_icon_falls_back_to_spinner():
    assert _normalize_starting_icon("coffee+spinner") == "spinner"
    assert _normalize_starting_icon("invalid") == "spinner"
    assert _normalize_starting_icon(None) == "spinner"


class FakeIdentityProvider:
    def __init__(self, token="", hashed_password=""):
        self.token = token
        self.hashed_password = hashed_password


def test_logout_is_available_only_for_token_or_password_authentication():
    assert not is_logout_available(FakeIdentityProvider())
    assert is_logout_available(FakeIdentityProvider(token="secret-token"))
    assert is_logout_available(FakeIdentityProvider(hashed_password="argon2:hash"))
    assert is_logout_available(
        FakeIdentityProvider(token="secret-token", hashed_password="argon2:hash")
    )


def test_logout_next_url_accepts_local_paths_under_base_url():
    assert _safe_logout_next_url("/mercury/demo?x=1", "/") == "/mercury/demo?x=1"
    assert (
        _safe_logout_next_url("/prefix/mercury/demo", "/prefix/")
        == "/prefix/mercury/demo"
    )


def test_logout_next_url_rejects_external_or_out_of_prefix_paths():
    assert _safe_logout_next_url("https://example.com", "/") == "/"
    assert _safe_logout_next_url("//example.com/path", "/") == "/"
    assert _safe_logout_next_url("/other/path", "/prefix/") == "/prefix/"
    assert _safe_logout_next_url("/prefix\\@example.com", "/prefix/") == "/prefix/"


class TestMercuryLogoutHandler(AsyncHTTPTestCase):
    def get_app(self):
        identity_provider = PasswordIdentityProvider(token="test-token")
        return Application(
            [(r"/prefix/mercury/logout", MercuryLogoutHandler)],
            base_url="/prefix/",
            identity_provider=identity_provider,
            cookie_secret="test-cookie-secret",
            allow_unauthenticated_access=True,
        )

    def test_logout_clears_cookie_and_redirects_to_login(self):
        response = self.fetch(
            "/prefix/mercury/logout?next=%2Fprefix%2Fmercury%2Fdemo",
            follow_redirects=False,
        )

        assert response.code == 302
        assert (
            response.headers["Location"]
            == "/prefix/login?next=%2Fprefix%2Fmercury%2Fdemo"
        )
        assert "Set-Cookie" in response.headers
