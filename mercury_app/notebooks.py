import json
import os

import tornado.web
from jupyter_server.base.handlers import JupyterHandler

from .notebooks_meta import list_notebooks


class NotebooksAPIHandler(JupyterHandler):
    """API endpoint to return list of notebooks discovered on disk."""

    @tornado.web.authenticated
    def get(self):
        base = self.settings.get("base_url", "") or ""

        # Defaults come from settings; both are optional.
        notebooks_dir = self.settings.get("notebooks_dir", os.getcwd())
        url_prefix = "mercury/"

        # Allow overriding via query params (optional)
        q_dir = self.get_argument("dir", default=None)
        if q_dir:
            notebooks_dir = q_dir
        recursive = self.get_argument("recursive", default="0") in {"1", "true", "True"}

        if not os.path.isdir(notebooks_dir):
            self.set_status(400)
            self.finish(json.dumps({"error": f"Notebooks directory '{notebooks_dir}' does not exist"}))
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
                "slug": href[:-6], # remove .ipynb extension
            }

            # Copy known extras if present
            extras = it.get("extras", {})
            for k in ("thumbnail_bg", "thumbnail_text", "thumbnail_text_color", "show_code"):
                if k in extras and extras[k] is not None:
                    rec[k] = extras[k]

            if "metadata_error" in it:
                rec["metadata_error"] = it["metadata_error"]

            notebooks.append(rec)

        self.set_header("Content-Type", "application/json")
        self.finish(json.dumps(notebooks))