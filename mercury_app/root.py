import os

import tornado.web
from jupyter_server.base.handlers import JupyterHandler
from jupyter_server.utils import url_path_join as ujoin
from tornado.httputil import url_concat

from mercury.config import build_theme_css_vars, build_theme_font_links

from .handlers import MAIN_CONFIG, THEME, WELCOME_CONFIG, is_logout_available
from .notebooks_meta import list_notebooks


def should_show_search_filter(notebooks: list[dict], main_config: dict) -> bool:
    if "show_search_filter" in main_config:
        return bool(main_config.get("show_search_filter"))
    return len(notebooks) > 3


def get_root_logout_url(identity_provider, base_url: str) -> str | None:
    """Return the root-page logout URL when token or password auth is enabled."""
    if not is_logout_available(identity_provider):
        return None

    normalized_base = base_url or "/"
    return url_concat(
        ujoin(normalized_base, "mercury/logout"),
        {"next": normalized_base},
    )


class RootIndexHandler(JupyterHandler):
    @tornado.web.authenticated
    def get(self):
        base = self.settings.get("base_url", "") or ""
        logout_url = get_root_logout_url(self.identity_provider, base)

        # Same defaults as the API handler
        notebooks_dir = self.settings.get("notebooks_dir", os.getcwd())
        url_prefix = "mercury/"
        recursive = bool(self.settings.get("notebooks_recursive", False))

        if not os.path.isdir(notebooks_dir):
            # Render an empty page with a friendly message instead of 400
            html = self.render_template(
                "root.html",
                notebooks=[],
                base_url=base,
                error=f"Notebooks directory '{notebooks_dir}' does not exist.",
                notebooks_button_label=MAIN_CONFIG.get("notebooks_button_label", "Notebooks"),
                logout_available=logout_url is not None,
                logout_url=logout_url,
                theme=THEME,
                theme_css_vars=build_theme_css_vars(THEME),
                theme_font_links=build_theme_font_links(THEME),
            )
            self.set_header("Content-Type", "text/html; charset=UTF-8")
            self.finish(html)
            return

        items = list_notebooks(notebooks_dir=notebooks_dir, recursive=recursive)

        notebooks = []
        for it in items:
            rel_path = it["rel_path"]
            href = f"{base}{url_prefix}{rel_path}"

            rec = {
                "name": it["name"],
                "description": it["description"],
                "href": href,
                "slug": href[:-6] # remove .ipynb file extension
            }

            # Copy known extras if present (keeps your template props working)
            extras = it.get("extras", {})
            for k in ("thumbnail_bg", "thumbnail_text", "thumbnail_text_color", "show_code"):
                if k in extras and extras[k] is not None:
                    rec[k] = extras[k]

            if "metadata_error" in it:
                rec["metadata_error"] = it["metadata_error"]

            notebooks.append(rec)

        default_welcome_msg = """
        <p class="lead"><b>Welcome to Mercury.</b> You're viewing notebooks turned into user-friendly apps.</p>
        <p class="lead2">Feel free to interact and explore - everything is designed to be <b>simple and safe</b>.</p>
        """

        html = self.render_template("root.html", notebooks=notebooks,
                                    base_url=base,
                                    title=MAIN_CONFIG.get("title", "Mercury"),
                                    footer=MAIN_CONFIG.get(
                                        "footer",
                                        "MLJAR - next generation of AI tools",
                                    ),
                                    header=WELCOME_CONFIG.get("header", "Hi there! 👋"),
                                    message=WELCOME_CONFIG.get(
                                        "message",
                                        default_welcome_msg,
                                    ),
                                    notebooks_button_label=MAIN_CONFIG.get(
                                        "notebooks_button_label",
                                        "Notebooks",
                                    ),
                                    search_filter_label=MAIN_CONFIG.get(
                                        "search_filter_label",
                                        "Search notebooks",
                                    ),
                                    show_search_filter=should_show_search_filter(
                                        notebooks,
                                        MAIN_CONFIG,
                                    ),
                                    logout_available=logout_url is not None,
                                    logout_url=logout_url,
                                    theme=THEME,
                                    theme_css_vars=build_theme_css_vars(THEME),
                                    theme_font_links=build_theme_font_links(THEME))
        self.set_header("Content-Type", "text/html; charset=UTF-8")
        self.finish(html)
