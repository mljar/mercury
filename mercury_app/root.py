import os

import tornado.web
from jupyter_server.base.handlers import JupyterHandler

from .handlers import MAIN_CONFIG, WELCOME_CONFIG
from .notebooks_meta import list_notebooks


class RootIndexHandler(JupyterHandler):
    @tornado.web.authenticated
    def get(self):
        base = self.settings.get("base_url", "") or ""

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
                error=f"Notebooks directory '{notebooks_dir}' does not exist."
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

        html = self.render_template("root.html", notebooks=notebooks, base_url=base, 
                                    title=MAIN_CONFIG.get("title", "Mercury"),           
                                    footer=MAIN_CONFIG.get("footer", "MLJAR - next generation of AI tools"),
                                    header=WELCOME_CONFIG.get("header", "Hi there! 👋"),
                                    message=WELCOME_CONFIG.get("message", default_welcome_msg))
        self.set_header("Content-Type", "text/html; charset=UTF-8")
        self.finish(html)
