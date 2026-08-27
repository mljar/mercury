from pathlib import Path

from jinja2 import Environment, FileSystemLoader


TEMPLATES_DIR = Path(__file__).parents[2] / "mercury_app" / "templates"


def template_environment():
    environment = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        extensions=["jinja2.ext.i18n"],
    )
    environment.install_null_translations()
    environment.globals.update(
        base_url="/",
        favicon_emoji="🌙",
        logged_in=False,
        login_available=True,
        page_title="Themed Mercury",
        static_url=lambda path: f"/static/{path}",
        theme_css_vars="--mercury-background-color: #112233;",
        theme_font_links='<link rel="stylesheet" href="https://fonts.example/theme.css">',
        token="",
        token_available=False,
        xsrf_form_html=lambda: '<input name="_xsrf">',
    )
    return environment


def test_login_template_includes_shared_theme_and_components():
    html = template_environment().get_template("login.html").render(
        message=None,
        next="/",
    )

    assert "--mercury-background-color: #112233;" in html
    assert "https://fonts.example/theme.css" in html
    assert 'class="mercury-page-card"' in html
    assert 'class="mercury-page-input"' in html
    assert 'class="mercury-page-button"' in html


def test_logout_template_includes_shared_theme_and_status_message():
    html = template_environment().get_template("logout.html").render(
        message={"info": "Successfully logged out."},
    )

    assert "--mercury-background-color: #112233;" in html
    assert 'class="mercury-page-message info"' in html
    assert "Successfully logged out." in html


def test_error_template_includes_shared_theme_and_error_card():
    html = template_environment().get_template("error.html").render(
        advices=["Try another page"],
        message="Details",
        status_code=404,
        status_message="Not Found",
    )

    assert "--mercury-background-color: #112233;" in html
    assert 'class="mercury-page-card error"' in html
    assert "404: Not Found" in html
    assert "Try another page" in html


def test_app_template_uses_versioned_static_url_for_bundle():
    html = template_environment().get_template("app.html").render(
        base_url="/",
        loading_message="Loading",
        page_config={"fullStaticUrl": "/static/mercury", "theme": {}},
        starting_icon="spinner",
        static=lambda path: f"/static/mercury/{path}?v=content-hash",
        ws_url="",
    )

    assert 'src="/static/mercury/bundle.js?v=content-hash"' in html
    assert 'src="/static/mercury/bundle.js"' not in html
