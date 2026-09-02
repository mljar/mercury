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

from mercury.config import build_theme_css_vars, build_theme_font_links

from ._version import __version__
from .block_handler import BLOCKED_PATTERNS, BlockedHandler
from .custom_contents_handler import MercuryContentsHandler
from .execution import (
    ExecutionRegistry,
    MercuryKernelWebsocketConnection,
    SharedSessionCoordinator,
)
from .execution.handlers import (
    MercuryCheckpointsHandler,
    MercuryKernelActionHandler,
    MercuryKernelHandler,
    MercuryMainKernelHandler,
    MercurySessionHandler,
    MercurySessionRootHandler,
)
from .execution.sync_handler import SharedSessionWebsocket
from .handlers import (
    MAIN_CONFIG,
    THEME,
    MercuryHandler,
    MercuryLogoutHandler,
    _normalize_starting_icon,
)
from .idle_timeout import (
    TimeoutActivityTransform,
    TimeoutManager,
)
from .mercury_hybrid_cm import HybridContentsManager
from .notebooks import NotebooksAPIHandler
from .root import RootIndexHandler
from .security_mode import detect_standalone_security_mode
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


def get_effective_notebooks_dir(serverapp) -> str:
    root_dir = getattr(serverapp, "root_dir", None)
    if root_dir:
        return os.path.abspath(root_dir)
    return os.getcwd()


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
        self.handlers.append(("/mercury/logout", MercuryLogoutHandler))
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
            security_handlers = [
                (
                    r"/mercury/api/shared-sessions/(?P<session_id>\w+-\w+-\w+-\w+-\w+)",
                    SharedSessionWebsocket,
                ),
                (
                    r"/api/contents/(.*\.ipynb)/checkpoints",
                    MercuryCheckpointsHandler,
                ),
                (r"/api/contents/(.*\.ipynb)", MercuryContentsHandler),
                (
                    r"/api/sessions/(?P<session_id>\w+-\w+-\w+-\w+-\w+)",
                    MercurySessionHandler,
                ),
                (r"/api/sessions", MercurySessionRootHandler),
                (
                    r"/api/kernels/(?P<kernel_id>\w+-\w+-\w+-\w+-\w+)/(?P<action>restart|interrupt)",
                    MercuryKernelActionHandler,
                ),
                (
                    r"/api/kernels/(?P<kernel_id>\w+-\w+-\w+-\w+-\w+)",
                    MercuryKernelHandler,
                ),
                (r"/api/kernels", MercuryMainKernelHandler),
            ]
            security_rules = []
            for pattern, handler in security_handlers:
                full_pattern = (base_url + pattern) if base_url else pattern
                security_rules.append(Rule(PathMatches(full_pattern), handler))
            app.default_router.rules = security_rules + block_rules + app.default_router.rules

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
                raise RuntimeError("Mercury execution firewall requires ServerApp")

            if getattr(sa, "disable_check_xsrf", False):
                raise RuntimeError(
                    "Mercury standalone mode requires XSRF protection; "
                    "remove --ServerApp.disable_check_xsrf=True"
                )

            registry = ExecutionRegistry()
            shared_session_coordinator = SharedSessionCoordinator()
            security_mode = detect_standalone_security_mode(sa)
            for settings in (self.settings, sa.web_app.settings):
                settings["mercury_execution_registry"] = registry
                settings["mercury_shared_session_coordinator"] = (
                    shared_session_coordinator
                )
                settings["mercury_security_mode"] = security_mode.value
                settings["kernel_websocket_connection_class"] = (
                    MercuryKernelWebsocketConnection
                )
            self.log.warning("Mercury security mode: %s", security_mode.value)

            cm = getattr(sa, "contents_manager", None)
            if not cm or getattr(cm, "_mercury_wrapped", False):
                return
            wrapped = HybridContentsManager.wrap(cm)
            setattr(wrapped, "_mercury_wrapped", True)
            sa.contents_manager = wrapped
            self.settings["contents_manager"] = wrapped

            self.settings["notebooks_dir"] = get_effective_notebooks_dir(sa)

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
                env.globals.setdefault("theme_css_vars", build_theme_css_vars(THEME))
                env.globals.setdefault("theme_font_links", build_theme_font_links(THEME))
                env.globals.setdefault(
                    "starting_icon",
                    _normalize_starting_icon(MAIN_CONFIG.get("starting_icon")),
                )
                env.globals.setdefault(
                    "starting_message",
                    MAIN_CONFIG.get("starting_message", "Initializing web application..."),
                )
            

    def initialize(self, argv=None):
        super().initialize()
        
        if hasattr(self, 'serverapp') and getattr(self, 'timeout', 0) > 0:
            self._timeout_manager = TimeoutManager(self.timeout, self.serverapp)
            self.serverapp.web_app._timeout_manager = self._timeout_manager
            self.serverapp.web_app.add_transform(TimeoutActivityTransform)

        
main = launch_new_instance = MercuryApp.launch_instance

if __name__ == "__main__":
    main()
