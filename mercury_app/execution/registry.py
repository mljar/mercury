from __future__ import annotations

import secrets
from dataclasses import dataclass, field

from tornado.web import HTTPError

from .manifest import NotebookExecutionManifest

OWNER_COOKIE = "mercury-browser-session"


@dataclass
class ExecutionSession:
    owners: set[str]
    session_id: str
    kernel_id: str
    manifest: NotebookExecutionManifest
    comm_ids: set[str] = field(default_factory=set)
    session_ids: set[str] = field(default_factory=set)


class ExecutionRegistry:
    def __init__(self, max_sessions_per_owner: int = 4, max_sessions: int = 256):
        self.max_sessions_per_owner = max_sessions_per_owner
        self.max_sessions = max_sessions
        self._sessions: dict[str, ExecutionSession] = {}
        self._kernels: dict[str, ExecutionSession] = {}

    def owner_for_handler(self, handler, *, create: bool) -> str | None:
        raw = handler.get_secure_cookie(OWNER_COOKIE)
        if raw:
            try:
                return raw.decode("ascii")
            except UnicodeDecodeError:
                pass
        if not create:
            return None
        owner = secrets.token_urlsafe(32)
        iframe_allow = bool(__import__("os").getenv("MERCURY_IFRAME_ALLOW"))
        handler.set_secure_cookie(
            OWNER_COOKIE,
            owner,
            httponly=True,
            secure=handler.request.protocol == "https" or iframe_allow,
            samesite="None" if iframe_allow else "Lax",
        )
        return owner

    def register(
        self,
        *,
        owner: str,
        session_id: str,
        kernel_id: str,
        manifest: NotebookExecutionManifest,
    ) -> ExecutionSession:
        owned = sum(1 for record in self._unique_records() if owner in record.owners)
        if owned >= self.max_sessions_per_owner:
            raise HTTPError(429, reason="Too many Mercury sessions")
        if len(self._unique_records()) >= self.max_sessions:
            raise HTTPError(503, reason="Mercury session capacity reached")
        record = ExecutionSession(
            {owner}, session_id, kernel_id, manifest, session_ids={session_id}
        )
        self._sessions[session_id] = record
        self._kernels[kernel_id] = record
        return record

    def session_for_owner(self, session_id: str, owner: str | None) -> ExecutionSession:
        record = self._sessions.get(session_id)
        if record is None or not owner or owner not in record.owners:
            raise HTTPError(404, reason="Session does not exist")
        return record

    def kernel_for_owner(self, kernel_id: str, owner: str | None) -> ExecutionSession:
        record = self._kernels.get(kernel_id)
        if record is None or not owner or owner not in record.owners:
            raise HTTPError(404, reason="Kernel does not exist")
        return record

    def sessions_for_owner(self, owner: str) -> list[ExecutionSession]:
        return [
            record
            for record in self._unique_records()
            if owner in record.owners
        ]

    def all_sessions(self) -> list[ExecutionSession]:
        return self._unique_records()

    def session_for_notebook(self, notebook_path: str) -> ExecutionSession | None:
        for record in self._sessions.values():
            if record.manifest.path == notebook_path:
                return record
        return None

    def attach_owner(
        self,
        session_id: str,
        owner: str,
        manifest: NotebookExecutionManifest,
    ) -> ExecutionSession:
        record = self._sessions.get(session_id)
        if record is None:
            raise HTTPError(404, reason="Session does not exist")
        if (
            record.manifest.path != manifest.path
            or record.manifest.revision != manifest.revision
        ):
            raise HTTPError(409, reason="Shared notebook revision changed")
        if owner not in record.owners:
            owned = sum(
                1 for current in self._unique_records() if owner in current.owners
            )
            if owned >= self.max_sessions_per_owner:
                raise HTTPError(429, reason="Too many Mercury sessions")
            record.owners.add(owner)
        return record

    def attach_session_alias(
        self,
        *,
        primary_session_id: str,
        alias_session_id: str,
        owner: str,
        manifest: NotebookExecutionManifest,
    ) -> ExecutionSession:
        record = self.attach_owner(primary_session_id, owner, manifest)
        record.session_ids.add(alias_session_id)
        self._sessions[alias_session_id] = record
        return record

    def unregister_session(self, session_id: str) -> None:
        record = self._sessions.get(session_id)
        if record is None:
            return
        if session_id != record.session_id:
            self._sessions.pop(session_id, None)
            record.session_ids.discard(session_id)
            return
        for current_id in list(record.session_ids):
            self._sessions.pop(current_id, None)
        self._kernels.pop(record.kernel_id, None)

    def _unique_records(self) -> list[ExecutionSession]:
        records: list[ExecutionSession] = []
        seen: set[str] = set()
        for record in self._sessions.values():
            if record.session_id not in seen:
                records.append(record)
                seen.add(record.session_id)
        return records
