# Copyright MLJAR Sp. z o.o.
# Licensed under the Apache License, Version 2.0 (Apache-2.0)

import logging
import os
import sys
from os.path import join as pjoin

from jupyterlab.commands import get_app_dir, get_user_settings_dir, get_workspaces_dir
from jupyterlab_server import LabServerApp
from tornado.routing import PathMatches, Rule
from traitlets import Bool, Integer

from ._version import __version__
from .block_handler import BLOCKED_PATTERNS, BlockedHandler
from .custom_contents_handler import MercuryContentsHandler
from .handlers import MAIN_CONFIG, MercuryHandler
from .idle_timeout import (
    TimeoutActivityTransform,
    TimeoutManager,
    patch_kernel_websocket_handler,
)
from .mercury_hybrid_cm import HybridContentsManager
from .notebooks import NotebooksAPIHandler
from .root import RootIndexHandler
from .theme_handler import ThemeHandler


class SuppressKernelDoesNotExist(logging.Filter):
    def filter(self, record):
        if 'Kernel does not exist:' in str(record.getMessage()):
            return False
        return True

for logger_name in ["tornado.application", "ServerApp"]:
    logger = logging.getLogger(logger_name)
    logger.addFilter(SuppressKernelDoesNotExist())

HERE = os.path.dirname(__file__)
app_dir = get_app_dir()
version = __version__


def is_mercury_app(argv0: str | None = None) -> bool:
    """
    Returns True when Mercury is started as the Mercury Standalone App,
    and False when imported as JupyterLab extension.
    """
    argv0 = argv0 if argv0 is not None else (sys.argv[0] if sys.argv else "")
    argv0 = (argv0 or "").replace("\\", "/")  # make Windows paths predictable
    return argv0.endswith("mercury_app/__main__.py") or argv0.endswith("mercury")

class MercuryApp(LabServerApp):
    name = "mercury"
    app_name = "Mercury"
    description = "Beautiful Web App from Python Notebook"
    version = version
    app_version = version
    extension_url = "/mercury"
    default_url = "/"
    file_url_prefix = "/mercury"
    load_other_extensions = True
    app_dir = app_dir
    app_settings_dir = pjoin(app_dir, "settings")
    schemas_dir = pjoin(app_dir, "schemas")
    themes_dir = pjoin(app_dir, "themes")
    user_settings_dir = get_user_settings_dir()
    workspaces_dir = get_workspaces_dir()
    subcommands = {}

    timeout = Integer(
        0,
        help="Timeout (in seconds) before shutting down if idle. 0 disables timeout."
    ).tag(config=True)

    keepSession = Bool(
        False,
        help="Keep the same session for all users."
    ).tag(config=True)

    aliases = {
        "timeout": "MercuryApp.timeout",
        "token": "IdentityProvider.token",
        "keep-session": "MercuryApp.keepSession"
    }

    def initialize_handlers(self):
        
        from jupyter_server.base.handlers import path_regex
        self.handlers.append((r"/", RootIndexHandler))
        self.handlers.append(("/mercury/api/notebooks", NotebooksAPIHandler))
        self.handlers.append(("/mercury/api/theme", ThemeHandler))
        self.handlers.append((f"/mercury{path_regex}", MercuryHandler))
        if sys.argv[0].endswith("mercury_app/__main__.py") or \
           sys.argv[0].endswith("mercury"):
            self.handlers.append((r"/api/contents/(.*\.ipynb)$", MercuryContentsHandler))
        super().initialize_handlers()

        # disable notebooks edit resources
        if is_mercury_app():
            sa = getattr(self, "serverapp", None)
            if not sa:
                return
            app = sa.web_app
            base_url = (sa.base_url or "").rstrip("/")
            block_rules = []
            for pat in BLOCKED_PATTERNS:
                full_pat = (base_url + pat) if base_url else pat
                block_rules.append(Rule(PathMatches(full_pat), BlockedHandler))
            app.default_router.rules = block_rules + app.default_router.rules

    def initialize_templates(self):
        super().initialize_templates()
        if is_mercury_app():
            self.static_dir = os.path.join(HERE, "static")
            static_paths = self.static_paths[:] if hasattr(self, "static_paths") else []
            if self.static_dir not in static_paths:
                static_paths.insert(0, self.static_dir)
            self.static_paths = static_paths

    def initialize_settings(self):
        super().initialize_settings()
        
        if is_mercury_app():
            sa = getattr(self, "serverapp", None)
            if not sa:
                return
            cm = getattr(sa, "contents_manager", None)
            if not cm or getattr(cm, "_mercury_wrapped", False):
                return
            wrapped = HybridContentsManager.wrap(cm)
            setattr(wrapped, "_mercury_wrapped", True)
            sa.contents_manager = wrapped
            self.settings["contents_manager"] = wrapped

            self.settings.setdefault("notebooks_dir", os.getcwd())

            from jinja2 import ChoiceLoader, FileSystemLoader
            templates_dir = os.path.join(HERE, "templates")
            loader = FileSystemLoader(templates_dir)

            env = self.settings.get("jinja2_env")
            if env is None:
                print("jinja2_env missing")
                return

            if isinstance(env.loader, ChoiceLoader):
                env.loader.loaders.insert(0, loader)
            else:
                env.loader = ChoiceLoader([loader, env.loader])

            if env:
                env.globals.setdefault("page_title", MAIN_CONFIG.get("title", "Mercury"))
                env.globals.setdefault("favicon_emoji", MAIN_CONFIG.get("favicon_emoji", "🎉"))
            

    def initialize(self, argv=None):
        super().initialize()
        
        if hasattr(self, 'serverapp') and getattr(self, 'timeout', 0) > 0:
            self._timeout_manager = TimeoutManager(self.timeout, self.serverapp)
            self.serverapp.web_app._timeout_manager = self._timeout_manager
            self.serverapp.web_app.add_transform(TimeoutActivityTransform)
            patch_kernel_websocket_handler()

        
main = launch_new_instance = MercuryApp.launch_instance

if __name__ == "__main__":
    main()
