from pathlib import Path

from jinja2 import Template

from mercury_app.root import get_root_logout_url, should_show_search_filter


class FakeIdentityProvider:
    def __init__(self, token="", hashed_password=""):
        self.token = token
        self.hashed_password = hashed_password


def render_root_template(**context):
    template_path = (
        Path(__file__).parents[2] / "mercury_app" / "templates" / "root.html"
    )
    return Template(template_path.read_text()).render(**context)


def test_should_show_search_filter_only_when_more_than_three_notebooks():
    assert should_show_search_filter([], {}) is False
    assert should_show_search_filter([{}, {}], {}) is False
    assert should_show_search_filter([{}, {}, {}], {}) is False
    assert should_show_search_filter([{}, {}, {}, {}], {}) is True


def test_should_show_search_filter_respects_config_toggle():
    assert should_show_search_filter([{}, {}, {}, {}], {"show_search_filter": False}) is False
    assert should_show_search_filter([], {"show_search_filter": True}) is True
    assert should_show_search_filter([{}, {}], {"show_search_filter": True}) is True


def test_root_logout_url_is_hidden_without_token_or_password():
    assert get_root_logout_url(FakeIdentityProvider(), "/") is None


def test_root_logout_url_returns_to_notebook_list_for_token_auth():
    assert (
        get_root_logout_url(FakeIdentityProvider(token="secret"), "/")
        == "/mercury/logout?next=%2F"
    )


def test_root_logout_url_respects_base_url_for_password_auth():
    assert (
        get_root_logout_url(
            FakeIdentityProvider(hashed_password="argon2:hash"),
            "/prefix/",
        )
        == "/prefix/mercury/logout?next=%2Fprefix%2F"
    )


def test_root_template_hides_logout_for_unprotected_server():
    html = render_root_template(
        notebooks=[],
        logout_available=False,
        logout_url=None,
    )

    assert 'id="logoutBtn"' not in html


def test_root_template_shows_logout_for_protected_server():
    html = render_root_template(
        notebooks=[],
        logout_available=True,
        logout_url="/mercury/logout?next=%2F",
    )

    assert 'id="logoutBtn"' in html
    assert 'href="/mercury/logout?next=%2F"' in html
    assert ">Log out</a>" in html
