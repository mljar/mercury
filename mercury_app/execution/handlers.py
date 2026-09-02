from __future__ import annotations

import json
import posixpath
from datetime import datetime, timezone

from jupyter_client.jsonutil import json_default
from jupyter_client.kernelspec import NoSuchKernel
from jupyter_server.auth.decorator import authorized
from jupyter_server.services.contents.handlers import ContentsAPIHandler
from jupyter_server.services.kernels.handlers import (
    KernelActionHandler,
    KernelHandler,
    MainKernelHandler,
)
from jupyter_server.services.sessions.handlers import SessionHandler, SessionRootHandler
from jupyter_server.utils import ensure_async, url_path_join
from tornado import web

from .manifest import ManifestError, NotebookExecutionManifest


def resolve_session_notebook_path(path, name) -> str:
    """Resolve JupyterLab's temporary session path to its shadow notebook."""
    if not isinstance(path, str) or not path:
        raise web.HTTPError(400, reason="A session path is required")
    if path.endswith(".ipynb"):
        return path
    if (
        isinstance(name, str)
        and name.endswith(".ipynb")
        and posixpath.basename(name) == name
    ):
        return posixpath.join(posixpath.dirname(path), name)
    raise web.HTTPError(400, reason="A notebook name is required")


class ExecutionHandlerMixin:
    @property
    def execution_registry(self):
        registry = self.settings.get("mercury_execution_registry")
        if registry is None:
            raise web.HTTPError(503, reason="Mercury execution firewall is unavailable")
        return registry

    def browser_owner(self, *, create: bool = True):
        return self.execution_registry.owner_for_handler(self, create=create)

    @property
    def keep_session(self) -> bool:
        return bool(self.settings.get("mercury_config", {}).get("keepSession", False))


class MercuryCheckpointsHandler(ContentsAPIHandler):
    """Expose the empty read-only checkpoint list expected by DocumentContext."""

    @web.authenticated
    @authorized
    async def get(self, path):
        if not path.endswith(".ipynb"):
            raise web.HTTPError(404)
        checkpoint = {
            "id": "mercury-readonly",
            "last_modified": datetime.now(timezone.utc).isoformat(),
        }
        self.finish(json.dumps([checkpoint]))

    @web.authenticated
    @authorized
    async def post(self, path):
        if not path.endswith(".ipynb"):
            raise web.HTTPError(404)
        checkpoint = {
            "id": "mercury-readonly",
            "last_modified": datetime.now(timezone.utc).isoformat(),
        }
        self.set_status(201)
        self.finish(json.dumps(checkpoint))


class MercurySessionRootHandler(ExecutionHandlerMixin, SessionRootHandler):
    @web.authenticated
    @authorized
    async def get(self):
        owner = self.browser_owner()
        models = []
        records = (
            self.execution_registry.all_sessions()
            if self.keep_session
            else self.execution_registry.sessions_for_owner(owner)
        )
        for record in records:
            try:
                if self.keep_session and owner not in record.owners:
                    self.execution_registry.attach_owner(
                        record.session_id, owner, record.manifest
                    )
                models.append(await self.session_manager.get_session(session_id=record.session_id))
            except KeyError:
                self.execution_registry.unregister_session(record.session_id)
        self.finish(json.dumps(models, default=json_default))

    @web.authenticated
    @authorized
    async def post(self):
        owner = self.browser_owner()
        model = self.get_json_body()
        if not isinstance(model, dict):
            self.log.warning("Rejected Mercury session without a JSON object")
            raise web.HTTPError(400, reason="No JSON data provided")
        self.log.debug(
            "Mercury session request: path=%r name=%r type=%r kernel=%r",
            model.get("path"),
            model.get("name"),
            model.get("type"),
            model.get("kernel"),
        )

        legacy_notebook = model.get("notebook")
        if isinstance(legacy_notebook, dict):
            model["path"] = legacy_notebook.get("path", legacy_notebook.get("name"))
            model["type"] = "notebook"
        path = model.get("path")
        name = model.get("name")
        try:
            notebook_path = resolve_session_notebook_path(path, name)
        except web.HTTPError:
            self.log.warning(
                "Rejected Mercury session notebook mapping: path=%r name=%r",
                path,
                name,
            )
            raise
        kernel = model.get("kernel") or {}
        if not isinstance(kernel, dict) or kernel.get("id"):
            self.log.warning(
                "Rejected Mercury session kernel attachment: type=%s has_id=%s",
                type(kernel).__name__,
                isinstance(kernel, dict) and bool(kernel.get("id")),
            )
            raise web.HTTPError(403, reason="Attaching an existing kernel is disabled")

        try:
            notebook_model = await ensure_async(
                self.contents_manager.get(
                    notebook_path, content=True, type="notebook", format="json"
                )
            )
            if notebook_model.get("type") != "notebook" or not isinstance(
                notebook_model.get("content"), dict
            ):
                raise ManifestError("Session path is not a notebook")
            manifest = NotebookExecutionManifest.from_notebook(
                notebook_path, notebook_model["content"]
            )
        except web.HTTPError:
            raise
        except Exception as exc:
            self.log.warning(
                "Rejected Mercury notebook manifest for %s: %s", notebook_path, exc
            )
            raise web.HTTPError(400, reason="Notebook cannot be executed safely") from exc

        sm = self.session_manager
        session_path = path
        coordinator = self.settings.get("mercury_shared_session_coordinator")
        lock = (
            coordinator.notebook_lock(notebook_path)
            if self.keep_session and coordinator is not None
            else None
        )

        async def attach_or_create():
            if self.keep_session:
                shared_record = self.execution_registry.session_for_notebook(
                    notebook_path
                )
                if shared_record is not None:
                    try:
                        await sm.get_session(
                            session_id=shared_record.session_id
                        )
                    except KeyError:
                        self.execution_registry.unregister_session(
                            shared_record.session_id
                        )
                    else:
                        if coordinator is not None:
                            await coordinator.wait_until_initialized(
                                shared_record.session_id
                            )
                        alias = await sm.create_session(
                            path=session_path,
                            kernel_id=shared_record.kernel_id,
                            name=model.get("name"),
                            type="notebook",
                        )
                        self.execution_registry.attach_session_alias(
                            primary_session_id=shared_record.session_id,
                            alias_session_id=alias["id"],
                            owner=owner,
                            manifest=manifest,
                        )
                        return alias, True
            elif await ensure_async(sm.session_exists(path=session_path)):
                existing = await sm.get_session(path=session_path)
                self.execution_registry.attach_owner(existing["id"], owner, manifest)
                return existing, False

            kernel_name = kernel.get("name")
            try:
                created = await sm.create_session(
                    path=session_path,
                    kernel_name=kernel_name,
                    name=model.get("name"),
                    type="notebook",
                )
            except NoSuchKernel as exc:
                raise web.HTTPError(
                    501, reason="Requested kernel is unavailable"
                ) from exc
            except Exception as exc:
                raise web.HTTPError(
                    500, reason="Notebook session could not be created"
                ) from exc

            try:
                self.execution_registry.register(
                    owner=owner,
                    session_id=created["id"],
                    kernel_id=created["kernel"]["id"],
                    manifest=manifest,
                )
            except Exception:
                await ensure_async(sm.delete_session(created["id"]))
                raise
            return created, True

        if lock is None:
            session_model, created = await attach_or_create()
        else:
            async with lock:
                session_model, created = await attach_or_create()

        if not created:
            location = url_path_join(
                self.base_url, "api", "sessions", session_model["id"]
            )
            self.set_header("Location", location)
            self.set_status(201)
            self.finish(json.dumps(session_model, default=json_default))
            return

        location = url_path_join(self.base_url, "api", "sessions", session_model["id"])
        self.set_header("Location", location)
        self.set_header("X-Mercury-Notebook-Revision", manifest.revision)
        self.set_status(201)
        self.finish(json.dumps(session_model, default=json_default))


class MercurySessionHandler(ExecutionHandlerMixin, SessionHandler):
    def _owned(self, session_id):
        return self.execution_registry.session_for_owner(
            session_id, self.browser_owner(create=False)
        )

    @web.authenticated
    @authorized
    async def get(self, session_id):
        self._owned(session_id)
        model = await self.session_manager.get_session(session_id=session_id)
        self.finish(json.dumps(model, default=json_default))

    @web.authenticated
    @authorized
    async def patch(self, session_id):
        record = self._owned(session_id)
        model = self.get_json_body()
        if not isinstance(model, dict):
            raise web.HTTPError(400, reason="No JSON data provided")
        self.log.debug("Mercury session patch %s: %r", session_id, model)
        if "id" in model and model["id"] != session_id:
            raise web.HTTPError(403, reason="Changing the session id is disabled")
        if "kernel" in model:
            raise web.HTTPError(403, reason="Changing a Mercury kernel is disabled")

        changes = {}
        if "path" in model:
            if model["path"] != record.manifest.path:
                raise web.HTTPError(403, reason="Changing the notebook path is disabled")
            changes["path"] = model["path"]
        if "name" in model:
            if model["name"] != posixpath.basename(record.manifest.path):
                raise web.HTTPError(403, reason="Changing the notebook name is disabled")
            changes["name"] = model["name"]
        if "type" in model:
            if model["type"] != "notebook":
                raise web.HTTPError(403, reason="Changing the session type is disabled")
            changes["type"] = "notebook"
        if set(model) - {"id", "path", "name", "type"}:
            raise web.HTTPError(403, reason="Unsupported Mercury session change")

        if changes:
            await self.session_manager.update_session(session_id, **changes)
        updated = await self.session_manager.get_session(session_id=session_id)
        self.finish(json.dumps(updated, default=json_default))

    @web.authenticated
    @authorized
    async def delete(self, session_id):
        self._owned(session_id)
        if self.keep_session:
            self.set_status(204)
            self.finish()
            return
        try:
            await self.session_manager.delete_session(session_id)
        except KeyError as exc:
            raise web.HTTPError(410, reason="Kernel deleted before session") from exc
        self.execution_registry.unregister_session(session_id)
        coordinator = self.settings.get("mercury_shared_session_coordinator")
        if coordinator is not None:
            coordinator.remove(session_id)
        self.set_status(204)
        self.finish()


class MercuryMainKernelHandler(ExecutionHandlerMixin, MainKernelHandler):
    @web.authenticated
    @authorized
    async def get(self):
        owner = self.browser_owner()
        models = []
        for record in self.execution_registry.sessions_for_owner(owner):
            try:
                models.append(await ensure_async(self.kernel_manager.kernel_model(record.kernel_id)))
            except KeyError:
                self.execution_registry.unregister_session(record.session_id)
        self.finish(json.dumps(models, default=json_default))

    @web.authenticated
    @authorized
    async def post(self):
        raise web.HTTPError(403, reason="Kernels must be created through a Mercury session")


class MercuryKernelHandler(ExecutionHandlerMixin, KernelHandler):
    def _owned(self, kernel_id):
        return self.execution_registry.kernel_for_owner(
            kernel_id, self.browser_owner(create=False)
        )

    @web.authenticated
    @authorized
    async def get(self, kernel_id):
        self._owned(kernel_id)
        model = await ensure_async(self.kernel_manager.kernel_model(kernel_id))
        self.finish(json.dumps(model, default=json_default))

    @web.authenticated
    @authorized
    async def delete(self, kernel_id):
        record = self._owned(kernel_id)
        if self.keep_session:
            self.set_status(204)
            self.finish()
            return
        await ensure_async(self.kernel_manager.shutdown_kernel(kernel_id))
        self.execution_registry.unregister_session(record.session_id)
        coordinator = self.settings.get("mercury_shared_session_coordinator")
        if coordinator is not None:
            coordinator.remove(record.session_id)
        self.set_status(204)
        self.finish()


class MercuryKernelActionHandler(ExecutionHandlerMixin, KernelActionHandler):
    @web.authenticated
    @authorized
    async def post(self, kernel_id, action):
        self.execution_registry.kernel_for_owner(
            kernel_id, self.browser_owner(create=False)
        )
        return await super().post(kernel_id, action)
