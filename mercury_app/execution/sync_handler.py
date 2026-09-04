from __future__ import annotations

import json
import secrets
from typing import Any

from jupyter_server.auth.decorator import ws_authenticated
from jupyter_server.base.handlers import JupyterHandler
from tornado import web, websocket

MAX_CONTROL_MESSAGE_BYTES = 64 * 1024


class SharedSessionWebsocket(JupyterHandler, websocket.WebSocketHandler):
    """Authenticated control channel for a shared Mercury session."""

    auth_resource = "kernels"

    @ws_authenticated
    async def get(self, *args, **kwargs):
        result = super().get(*args, **kwargs)
        if result is not None:
            await result

    def set_default_headers(self):
        # JupyterHandler's HTTP security headers do not apply to WebSockets.
        return None

    def get_compression_options(self):
        return self.settings.get("websocket_compression_options", None)

    def open(self, session_id: str):
        registry = self.settings.get("mercury_execution_registry")
        coordinator = self.settings.get("mercury_shared_session_coordinator")
        if registry is None or coordinator is None:
            raise web.HTTPError(503, reason="Shared sessions are unavailable")

        owner = registry.owner_for_handler(self, create=False)
        record = registry.session_for_owner(session_id, owner)
        # Alias Jupyter sessions share the primary Mercury session's kernel and
        # therefore must also share its coordinator room.  Using the URL alias
        # here would grant a lease that the kernel connection cannot validate.
        self.session_id = record.session_id
        self.client_id = secrets.token_urlsafe(24)
        self._coordinator = coordinator
        coordinator.join(
            session_id=self.session_id,
            kernel_id=record.kernel_id,
            cell_count=record.manifest.cell_count,
            client=self,
        )

    def on_message(self, raw_message: str | bytes):
        if isinstance(raw_message, bytes):
            if len(raw_message) > MAX_CONTROL_MESSAGE_BYTES:
                self.close(code=1009, reason="Shared-session message is too large")
                return
            raw_message = raw_message.decode("utf-8")
        elif len(raw_message.encode("utf-8")) > MAX_CONTROL_MESSAGE_BYTES:
            self.close(code=1009, reason="Shared-session message is too large")
            return

        try:
            message = json.loads(raw_message)
            if not isinstance(message, dict):
                raise ValueError("Shared-session message must be an object")
            message_type = message.get("type")
            if message_type == "rerun_request":
                from_index = message.get("from_index")
                recovery = message.get("recovery", False)
                if not isinstance(from_index, int) or isinstance(from_index, bool):
                    raise ValueError("rerun_request requires an integer from_index")
                if not isinstance(recovery, bool):
                    raise ValueError("rerun_request recovery must be a boolean")
                self._coordinator.request_run(
                    self.session_id,
                    self.client_id,
                    from_index,
                    prefer_other=recovery,
                )
            elif message_type == "run_complete":
                run_id = message.get("run_id")
                token = message.get("token")
                if not isinstance(run_id, int) or not isinstance(token, str):
                    raise ValueError("run_complete requires run_id and token")
                self._coordinator.complete_run(
                    self.session_id, self.client_id, run_id, token
                )
            else:
                raise ValueError("Unsupported shared-session message")
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            self.send_shared_session_message(
                {"type": "error", "message": str(exc)}
            )

    def on_close(self):
        coordinator = getattr(self, "_coordinator", None)
        session_id = getattr(self, "session_id", None)
        client_id = getattr(self, "client_id", None)
        if coordinator is not None and session_id and client_id:
            coordinator.leave(session_id, client_id)

    def send_shared_session_message(self, message: dict[str, Any]) -> None:
        if self.ws_connection is not None:
            self.write_message(json.dumps(message, separators=(",", ":")))
