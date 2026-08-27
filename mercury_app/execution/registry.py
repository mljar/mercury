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
        owned = sum(1 for record in self._sessions.values() if owner in record.owners)
        if owned >= self.max_sessions_per_owner:
            raise HTTPError(429, reason="Too many Mercury sessions")
        if len(self._sessions) >= self.max_sessions:
            raise HTTPError(503, reason="Mercury session capacity reached")
        record = ExecutionSession({owner}, session_id, kernel_id, manifest)
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
        return [record for record in self._sessions.values() if owner in record.owners]

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
                1 for current in self._sessions.values() if owner in current.owners
            )
            if owned >= self.max_sessions_per_owner:
                raise HTTPError(429, reason="Too many Mercury sessions")
            record.owners.add(owner)
        return record

    def unregister_session(self, session_id: str) -> None:
        record = self._sessions.pop(session_id, None)
        if record is not None:
            self._kernels.pop(record.kernel_id, None)
