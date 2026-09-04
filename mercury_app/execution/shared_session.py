from __future__ import annotations

import asyncio
import secrets
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Protocol

MAX_SNAPSHOT_EVENTS_PER_CELL = 512
MAX_SEEN_KERNEL_MESSAGES = 4096


class SharedSessionClient(Protocol):
    client_id: str

    def send_shared_session_message(self, message: dict[str, Any]) -> None: ...


@dataclass(frozen=True)
class RunLease:
    run_id: int
    token: str
    client_id: str
    from_index: int
    initialize: bool = False


@dataclass
class SharedSessionRoom:
    session_id: str
    kernel_id: str
    cell_count: int
    clients: dict[str, SharedSessionClient] = field(default_factory=dict)
    initialized: bool = False
    revision: int = 0
    active_run: RunLease | None = None
    pending_from_index: int | None = None
    executions: dict[str, dict[str, Any]] = field(default_factory=dict)
    outputs: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    seen_kernel_messages: set[str] = field(default_factory=set)
    seen_kernel_message_order: deque[str] = field(default_factory=deque)

    def send(self, client_id: str, message: dict[str, Any]) -> None:
        client = self.clients.get(client_id)
        if client is not None:
            client.send_shared_session_message(message)

    def broadcast(self, message: dict[str, Any]) -> None:
        for client in list(self.clients.values()):
            client.send_shared_session_message(message)


class SharedSessionCoordinator:
    """Coordinate one execution stream for every shared Mercury session."""

    def __init__(self) -> None:
        self._rooms: dict[str, SharedSessionRoom] = {}
        self._notebook_locks: dict[str, asyncio.Lock] = {}
        self._initialized_events: dict[str, asyncio.Event] = {}

    def notebook_lock(self, notebook_path: str) -> asyncio.Lock:
        lock = self._notebook_locks.get(notebook_path)
        if lock is None:
            lock = asyncio.Lock()
            self._notebook_locks[notebook_path] = lock
        return lock

    async def wait_until_initialized(
        self, session_id: str, timeout: float = 30.0
    ) -> bool:
        room = self._rooms.get(session_id)
        if room is not None and room.initialized:
            return True
        event = self._initialized_events.setdefault(session_id, asyncio.Event())
        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
        except TimeoutError:
            return False
        return True

    def join(
        self,
        *,
        session_id: str,
        kernel_id: str,
        cell_count: int,
        client: SharedSessionClient,
    ) -> SharedSessionRoom:
        room = self._rooms.get(session_id)
        if room is None:
            room = SharedSessionRoom(session_id, kernel_id, cell_count)
            self._rooms[session_id] = room
        elif room.kernel_id != kernel_id:
            raise ValueError("Shared session kernel changed")

        room.clients[client.client_id] = client
        client.send_shared_session_message(
            {
                "type": "welcome",
                "session_id": session_id,
                "initialized": room.initialized,
                "revision": room.revision,
                "client_id": client.client_id,
                "outputs": room.outputs,
            }
        )

        if not room.initialized and room.active_run is None:
            self._grant(room, client.client_id, 0, initialize=True)
        elif room.active_run is None and room.pending_from_index is not None:
            self._grant_pending(room, preferred_client=client.client_id)
        else:
            room.broadcast(
                {
                    "type": "presence",
                    "clients": len(room.clients),
                    "revision": room.revision,
                }
            )
        return room

    def leave(self, session_id: str, client_id: str) -> None:
        room = self._rooms.get(session_id)
        if room is None:
            return
        room.clients.pop(client_id, None)

        active = room.active_run
        if active is not None and active.client_id == client_id:
            room.active_run = None
            retry_from = active.from_index
            if room.pending_from_index is not None:
                retry_from = min(retry_from, room.pending_from_index)
            room.pending_from_index = retry_from
            self._grant_pending(room)

        if room.clients:
            room.broadcast(
                {
                    "type": "presence",
                    "clients": len(room.clients),
                    "revision": room.revision,
                }
            )

    def request_run(
        self,
        session_id: str,
        client_id: str,
        from_index: int,
        *,
        prefer_other: bool = False,
    ) -> RunLease | None:
        room = self._require_room(session_id)
        self._validate_client(room, client_id)
        if from_index < 0 or from_index > room.cell_count:
            raise ValueError("Invalid rerun cell index")

        if room.active_run is not None or not room.initialized:
            room.pending_from_index = (
                from_index
                if room.pending_from_index is None
                else min(room.pending_from_index, from_index)
            )
            return None
        preferred_client = client_id
        if prefer_other:
            preferred_client = next(
                (
                    connected_id
                    for connected_id in room.clients
                    if connected_id != client_id
                ),
                client_id,
            )
        return self._grant(room, preferred_client, from_index)

    def complete_run(
        self, session_id: str, client_id: str, run_id: int, token: str
    ) -> None:
        room = self._require_room(session_id)
        active = room.active_run
        if (
            active is None
            or active.client_id != client_id
            or active.run_id != run_id
            or not secrets.compare_digest(active.token, token)
        ):
            raise ValueError("Stale or invalid shared-session run lease")

        room.active_run = None
        room.initialized = True
        self._initialized_events.setdefault(session_id, asyncio.Event()).set()
        room.revision += 1
        room.broadcast(
            {
                "type": "run_complete",
                "run_id": run_id,
                "revision": room.revision,
            }
        )
        self._grant_pending(room, preferred_client=client_id)

    def validate_lease(
        self, session_id: str, client_id: str, run_id: int, token: str
    ) -> RunLease:
        room = self._require_room(session_id)
        active = room.active_run
        if (
            active is None
            or active.client_id != client_id
            or active.run_id != run_id
            or not secrets.compare_digest(active.token, token)
        ):
            expected = (
                "none"
                if active is None
                else f"run {active.run_id} for client {active.client_id}"
            )
            raise ValueError(
                "Shared-session execution has no valid lease "
                f"(received run {run_id} for client {client_id}; expected {expected})"
            )
        return active

    def register_execute(
        self,
        *,
        session_id: str,
        client_id: str,
        run_id: int,
        token: str,
        message_id: str,
        cell_id: str,
    ) -> None:
        room = self._require_room(session_id)
        self.validate_lease(session_id, client_id, run_id, token)
        if not message_id or not cell_id:
            raise ValueError("Shared execution requires message and cell ids")
        room.executions[message_id] = {
            "cell_id": cell_id,
            "client_id": client_id,
            "run_id": run_id,
            "seen_visible": False,
            "clear_pending": False,
        }

    def observe_kernel_message(
        self, session_id: str, message: dict[str, Any]
    ) -> None:
        room = self._rooms.get(session_id)
        if room is None:
            return
        header = message.get("header")
        parent_header = message.get("parent_header")
        if not isinstance(header, dict) or not isinstance(parent_header, dict):
            return
        message_id = header.get("msg_id")
        parent_id = parent_header.get("msg_id")
        message_type = header.get("msg_type")
        if not all(isinstance(value, str) for value in (message_id, parent_id, message_type)):
            return
        if message_id in room.seen_kernel_messages:
            return
        room.seen_kernel_messages.add(message_id)
        room.seen_kernel_message_order.append(message_id)
        while len(room.seen_kernel_message_order) > MAX_SEEN_KERNEL_MESSAGES:
            expired = room.seen_kernel_message_order.popleft()
            room.seen_kernel_messages.discard(expired)

        execution = room.executions.get(parent_id)
        if execution is None:
            return
        if message_type == "status":
            content = message.get("content")
            if isinstance(content, dict) and content.get("execution_state") == "idle":
                room.executions.pop(parent_id, None)
            return
        if message_type not in {
            "stream",
            "display_data",
            "execute_result",
            "update_display_data",
            "error",
            "clear_output",
        }:
            return

        cell_id = execution["cell_id"]
        content = message.get("content")
        reset = False
        if message_type == "clear_output":
            wait = isinstance(content, dict) and content.get("wait") is True
            if wait:
                execution["clear_pending"] = True
            else:
                room.outputs[cell_id] = []
                reset = True
        elif message_type in {"stream", "display_data", "execute_result", "error"}:
            if not execution["seen_visible"] or execution["clear_pending"]:
                room.outputs[cell_id] = []
                execution["seen_visible"] = True
                execution["clear_pending"] = False
                reset = True

        event = {
            "header": header,
            "parent_header": parent_header,
            "metadata": message.get("metadata", {}),
            "content": content if isinstance(content, dict) else {},
        }
        if message_type != "clear_output" or not reset:
            cell_outputs = room.outputs.setdefault(cell_id, [])
            cell_outputs.append(event)
            if len(cell_outputs) > MAX_SNAPSHOT_EVENTS_PER_CELL:
                del cell_outputs[: -MAX_SNAPSHOT_EVENTS_PER_CELL]
        room.broadcast(
            {
                "type": "output",
                "cell_id": cell_id,
                "run_id": execution["run_id"],
                "executor_client_id": execution["client_id"],
                "reset": reset,
                "message": event,
            }
        )

    def remove(self, session_id: str) -> None:
        room = self._rooms.pop(session_id, None)
        if room is not None:
            room.broadcast({"type": "session_closed"})
        self._initialized_events.pop(session_id, None)

    def room(self, session_id: str) -> SharedSessionRoom | None:
        return self._rooms.get(session_id)

    def _grant_pending(
        self, room: SharedSessionRoom, preferred_client: str | None = None
    ) -> RunLease | None:
        if room.active_run is not None or not room.clients:
            return None
        from_index = room.pending_from_index
        if from_index is None:
            if room.initialized:
                return None
            from_index = 0
        room.pending_from_index = None
        client_id = (
            preferred_client
            if preferred_client in room.clients
            else next(iter(room.clients))
        )
        return self._grant(
            room, client_id, from_index, initialize=not room.initialized
        )

    def _grant(
        self,
        room: SharedSessionRoom,
        client_id: str,
        from_index: int,
        *,
        initialize: bool = False,
    ) -> RunLease:
        lease = RunLease(
            run_id=room.revision + 1,
            token=secrets.token_urlsafe(32),
            client_id=client_id,
            from_index=from_index,
            initialize=initialize,
        )
        room.active_run = lease
        room.send(
            client_id,
            {
                "type": "run",
                "run_id": lease.run_id,
                "token": lease.token,
                "from_index": lease.from_index,
                "initialize": lease.initialize,
            },
        )
        room.broadcast(
            {
                "type": "busy",
                "run_id": lease.run_id,
                "from_index": lease.from_index,
            }
        )
        return lease

    def _require_room(self, session_id: str) -> SharedSessionRoom:
        room = self._rooms.get(session_id)
        if room is None:
            raise ValueError("Shared session is not connected")
        return room

    @staticmethod
    def _validate_client(room: SharedSessionRoom, client_id: str) -> None:
        if client_id not in room.clients:
            raise ValueError("Shared-session client is not connected")
