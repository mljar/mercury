# Copyright MLJAR Sp. z o.o.
# Licensed under the Apache License, Version 2.0 (Apache-2.0)

import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

import toml
from jupyter_server.base.handlers import JupyterHandler
from jupyter_server.extension.handler import (
    ExtensionHandlerJinjaMixin,
    ExtensionHandlerMixin,
)
from jupyter_server.utils import ensure_async
from jupyter_server.utils import url_path_join as ujoin
from jupyterlab_server.config import LabConfig, get_page_config, recursive_update
from jupyterlab_server.handlers import _camelCase, is_url
from tornado import web

from ._version import __version__

version = __version__


def load_config(config_path="config.toml"):
    config_file = Path(config_path)
    if not config_file.exists():
        return {"theme": {}, "main": {}, "welcome": {}}

    config = toml.load(config_file)
    return {
        "theme": config.get("theme", {}),
        "main": config.get("main", {}),
        "welcome": config.get("welcome", {})
    }


CONFIG = load_config()
THEME = CONFIG["theme"]
MAIN_CONFIG = CONFIG["main"]
WELCOME_CONFIG = CONFIG["welcome"]


def _to_posix(p: str) -> str:
    """Normalize filesystem-like path to Jupyter API posix (forward slashes)."""
    return str(Path(p).as_posix())


class MercuryHandler(ExtensionHandlerJinjaMixin, ExtensionHandlerMixin, JupyterHandler):
    """Render the Mercury app with per-window isolated sessions via shadow notebooks."""

    def get_page_config(self, notebook_path: Optional[str] = None):
        config = LabConfig()
        app = self.extensionapp
        base_url = self.settings.get("base_url")

        page_config = {
            "appVersion": version,
            "baseUrl": self.base_url,
            "terminalsAvailable": False,
            "token": self.settings["token"],
            "fullStaticUrl": ujoin(self.base_url, "static", self.name),
            "frontendUrl": ujoin(self.base_url, "mercury/"),
            "notebookPath": notebook_path,
            "title": MAIN_CONFIG.get("title", "Mercury")
        }

        mathjax_config = self.settings.get("mathjax_config", "TeX-AMS_HTML-full,Safe")
        mathjax_url = self.settings.get(
            "mathjax_url",
            "https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js",
        )
        page_config.setdefault("mathjaxConfig", mathjax_config)
        page_config.setdefault("fullMathjaxUrl", mathjax_url)

        for name in config.trait_names():
            page_config[_camelCase(name)] = getattr(app, name)

        for name in config.trait_names():
            if not name.endswith("_url"):
                continue
            full_name = _camelCase("full_" + name)
            full_url = getattr(app, name)
            if not is_url(full_url):
                full_url = ujoin(base_url, full_url)
            page_config[full_name] = full_url

        labextensions_path = app.extra_labextensions_path + app.labextensions_path
        recursive_update(
            page_config,
            get_page_config(
                labextensions_path,
                logger=self.log,
            ),
        )
        return page_config

    def _get_keep_session(self) -> bool:
        """Global default + optional ?keepSession=true|false override."""
        keep_session = self.settings.get('mercury_config', {}).get('keepSession', False)
        #arg = self.get_argument("keepSession", default=None)
        #if arg is not None:
        #    keep_session = arg.lower() in ("1", "true", "yes", "y")
        return keep_session

    def _get_ttl_hours(self) -> int:
        """Shadow file TTL (hours) from settings, default 12h."""
        return 12 #int(self.settings.get('mercury_config', {}).get('shadow_ttl_hours', 12))

    async def _ensure_dir(self, dir_path: str):
        """Ensure a directory exists via ContentsManager."""
        cm = self.serverapp.contents_manager
        exists = await ensure_async(cm.dir_exists(dir_path))
        if not exists:
            self.log.info("[Mercury] Creating shadow dir: %s", dir_path)
            await ensure_async(cm.save({'type': 'directory'}, dir_path))

    def _shadow_dir_for(self, nb_path: str) -> str:
        """
        Return posix path for the shadow folder next to the notebook:
        e.g. for 'folder/plots.ipynb' => 'folder/.mercury_sessions'
        """
        p = Path(nb_path)
        parent = _to_posix(p.parent)
        return f"{parent}/.mercury_sessions"

    async def _copy_notebook_to_shadow(self, src_path: str) -> str:
        """
        Create a per-window shadow copy of the notebook under a unique path,
        using the server's ContentsManager so the frontend can open it normally.
        """
        cm = self.serverapp.contents_manager
        src = await ensure_async(cm.get(src_path, content=True))
        if src.get('type') != 'notebook':
            raise web.HTTPError(400, f"Expected a notebook; got {src.get('type')}")

        shadow_dir = self._shadow_dir_for(src_path)
        await self._ensure_dir(shadow_dir)

        p = Path(src_path)
        shadow_name = f"{p.stem}__mercury__{uuid.uuid4().hex[:8]}{p.suffix}"
        shadow_path = f"{shadow_dir}/{shadow_name}"

        model = {
            'type': 'notebook',
            'format': 'json',
            'content': src['content'],
        }
        await ensure_async(cm.save(model, shadow_path))
        return shadow_path  # posix path

    async def _list_active_session_paths(self) -> List[str]:
        """Collect all session paths currently in use."""
        mgr = self.serverapp.session_manager
        sessions = await ensure_async(mgr.list_sessions())
        paths: List[str] = []
        for m in sessions:
            # model path can be 'path' or nested in 'notebook' depending on server versions
            mp = m.get("path") or (m.get("notebook") or {}).get("path")
            if mp:
                paths.append(mp)
        return paths

    async def _cleanup_shadows(self, nb_path: str):
        """
        Delete shadow notebooks that are:
          - inside the .mercury_sessions folder next to nb_path
          - not used by any active session
          - older than TTL (hours)
        """
        cm = self.serverapp.contents_manager
        shadow_dir = self._shadow_dir_for(nb_path)
        ttl_hours = self._get_ttl_hours()
        cutoff = datetime.now(timezone.utc) - timedelta(hours=ttl_hours)

        # If no shadow dir, nothing to do
        if not await ensure_async(cm.dir_exists(shadow_dir)):
            return

        try:
            listing = await ensure_async(cm.get(shadow_dir, content=True))
        except Exception as e:
            self.log.warning("[Mercury] Could not list shadow dir %s: %s", shadow_dir, e)
            return

        if listing.get('type') != 'directory' or not listing.get('content'):
            return

        active_paths = set(await self._list_active_session_paths())
        removed = 0

        for entry in listing['content']:
            if entry.get('type') != 'notebook':
                # Optionally remove stray files older than TTL
                continue

            spath = entry.get('path')
            if not spath:
                continue

            # Keep if in use by a session
            if spath in active_paths:
                continue

            # Check age (entry['last_modified'] is ISO timestamp; already tz-aware)
            lm = entry.get('last_modified')
            try:
                # Some ContentsManagers return aware datetimes, some strings.
                if isinstance(lm, str):
                    # Naive fallback parsing; in most Jupyter servers it's already datetime
                    lm_dt = datetime.fromisoformat(lm.replace('Z', '+00:00'))
                else:
                    lm_dt = lm
            except Exception:
                lm_dt = cutoff  # be permissive → allow deletion

            if lm_dt <= cutoff:
                try:
                    await ensure_async(cm.delete(spath))
                    removed += 1
                except Exception as e:
                    self.log.warning("[Mercury] Failed to delete shadow %s: %s", spath, e)

        if removed:
            self.log.info("[Mercury] Cleanup removed %d shadow notebook(s) in %s", removed, shadow_dir)

        # Optional: remove empty shadow dir
        try:
            listing2 = await ensure_async(cm.get(shadow_dir, content=True))
            if not listing2.get('content'):
                await ensure_async(cm.delete(shadow_dir))
                self.log.info("[Mercury] Removed empty shadow dir %s", shadow_dir)
        except Exception:
            pass

    @web.authenticated
    async def get(self, path: str = None):
        self.log.info("[Mercury] GET %s", path)
        if not path.endswith(".ipynb"):
            path += ".ipynb"
        # Validate the source notebook path
        if not (
            path
            and await ensure_async(self.serverapp.contents_manager.file_exists(path))
            and Path(path).suffix == ".ipynb"
        ):
            message = (
                f"Only Jupyter Notebook can be opened with Mercury; got {path}"
                if path else "No Jupyter Notebook specified."
            )
            return self.write(
                self.render_template(
                    "error.html",
                    default_url="https://runmercury.com/",
                    static=self.static_url,
                    page_title="Mercury",
                    status_code=404,
                    status_message=message,
                    advices=["You must provide a valid notebook path"],
                )
            )

        # Build page config
        page_config = self.get_page_config(path)
        page_config["theme"] = THEME

        keep_session = self._get_keep_session()
        self.log.info("[Mercury] keepSession=%s", keep_session)

        # Opportunistic cleanup (best effort, non-blocking if it fails)
        try:
            await self._cleanup_shadows(path)
        except Exception as e:
            self.log.warning("[Mercury] Cleanup pass failed: %s", e)

        # Decide what notebook path the frontend should open
        effective_notebook_path = path
        if not keep_session:
            try:
                effective_notebook_path = await self._copy_notebook_to_shadow(path)
                self.log.info("[Mercury] Shadow notebook path: %s", effective_notebook_path)
            except Exception as e:
                self.log.error("[Mercury] Failed to create shadow notebook; falling back to shared session: %s", e)
                effective_notebook_path = path  # shared

        # Hand the final path to the frontend (no frontend changes!)
        page_config["notebookPath"] = effective_notebook_path
        page_config["keepSession"] = keep_session

        return self.write(
            self.render_template(
                "app.html",
                static=self.static_url,
                base_url=self.base_url,
                token=self.settings["token"],
                page_config=page_config,
            )
        )
