from __future__ import annotations

import json
import logging
from collections.abc import Mapping

from jupyter_server.services.kernels.connection.channels import (
    ZMQChannelsWebsocketConnection,
    deserialize_binary_message,
    deserialize_msg_from_ws_v1,
)

from .policy import ExecutionDenied, authorize_execute_request

logger = logging.getLogger("mercury.execution")

MAX_MESSAGE_BYTES = 128 * 1024 * 1024
MAX_COMM_DATA_BYTES = 2 * 1024 * 1024
INFO_MESSAGES = {"kernel_info_request", "comm_info_request"}
COMM_MESSAGES = {"comm_msg", "comm_close"}
FRONTEND_COMM_TARGETS = {"jupyter.widget.control"}


class MercuryKernelWebsocketConnection(ZMQChannelsWebsocketConnection):
    """Jupyter websocket transport that enforces Mercury's execution policy."""

    async def prepare(self):
        handler = self.websocket_handler
        registry = handler.settings.get("mercury_execution_registry")
        if registry is None:
            raise RuntimeError("Mercury execution registry is not installed")
        owner = registry.owner_for_handler(handler, create=False)
        self._mercury_record = registry.kernel_for_owner(self.kernel_id, owner)
        self._shared_session_coordinator = handler.settings.get(
            "mercury_shared_session_coordinator"
        )
        await super().prepare()

    def _deny(self, reason: str) -> None:
        logger.warning("Rejected kernel websocket message: %s", reason)
        self.websocket_handler.close(code=1008, reason="Kernel request denied")

    @staticmethod
    def _serialized_size(value) -> int:
        try:
            return len(json.dumps(value, ensure_ascii=False).encode("utf-8"))
        except (TypeError, ValueError):
            raise ExecutionDenied("Message contains invalid JSON data") from None

    def _authorize_message(self, channel: str, msg: dict) -> dict:
        header = msg.get("header")
        metadata = msg.get("metadata", {})
        content = msg.get("content", {})
        buffers = msg.get("buffers", [])
        if not isinstance(header, Mapping) or not isinstance(metadata, Mapping):
            raise ExecutionDenied("Malformed kernel message")
        if not isinstance(content, Mapping):
            raise ExecutionDenied("Malformed kernel message content")
        if channel not in {"shell", "control", "stdin"}:
            raise ExecutionDenied("Kernel channel is not allowed")
        if sum(len(buffer) for buffer in buffers) > MAX_MESSAGE_BYTES:
            raise ExecutionDenied("Kernel buffers are too large")

        msg_type = header.get("msg_type")
        if msg_type == "execute_request":
            if channel != "shell":
                raise ExecutionDenied("Execution is allowed only on the shell channel")
            decision = authorize_execute_request(metadata, self._mercury_record.manifest)
            safe_content = dict(content)
            safe_content["code"] = decision.code
            safe_content["allow_stdin"] = False
            safe_content["user_expressions"] = {}
            msg["content"] = safe_content
            coordinator = getattr(self, "_shared_session_coordinator", None)
            room = (
                coordinator.room(self._mercury_record.session_id)
                if coordinator is not None
                else None
            )
            if room is not None and decision.kind == "cell":
                mercury = metadata.get("mercury")
                shared = (
                    mercury.get("shared_session")
                    if isinstance(mercury, Mapping)
                    else None
                )
                if not isinstance(shared, Mapping):
                    raise ExecutionDenied("Shared execution is missing a run lease")
                client_id = shared.get("client_id")
                run_id = shared.get("run_id")
                token = shared.get("token")
                cell_id = mercury.get("cell_id")
                message_id = header.get("msg_id")
                if (
                    not isinstance(client_id, str)
                    or not isinstance(run_id, int)
                    or not isinstance(token, str)
                    or not isinstance(cell_id, str)
                    or not isinstance(message_id, str)
                ):
                    raise ExecutionDenied("Shared execution has an invalid run lease")
                try:
                    coordinator.register_execute(
                        session_id=self._mercury_record.session_id,
                        client_id=client_id,
                        run_id=run_id,
                        token=token,
                        message_id=message_id,
                        cell_id=cell_id,
                    )
                except ValueError as exc:
                    raise ExecutionDenied(str(exc)) from exc
            return msg

        if msg_type in INFO_MESSAGES:
            if channel != "shell":
                raise ExecutionDenied("Information request used an invalid channel")
            return msg

        if msg_type == "comm_open":
            if channel != "shell":
                raise ExecutionDenied("Comm message used an invalid channel")
            comm_id = content.get("comm_id")
            target_name = content.get("target_name")
            if not isinstance(comm_id, str) or target_name not in FRONTEND_COMM_TARGETS:
                raise ExecutionDenied("Browser-created comm target is not allowed")
            self._mercury_record.comm_ids.add(comm_id)
            return msg

        if msg_type in COMM_MESSAGES:
            if channel != "shell":
                raise ExecutionDenied("Comm message used an invalid channel")
            comm_id = content.get("comm_id")
            if not isinstance(comm_id, str) or comm_id not in self._mercury_record.comm_ids:
                raise ExecutionDenied("Comm id is not registered for this kernel")
            if self._serialized_size(content.get("data", {})) > MAX_COMM_DATA_BYTES:
                raise ExecutionDenied("Comm payload is too large")
            if msg_type == "comm_close":
                self._mercury_record.comm_ids.discard(comm_id)
            return msg

        raise ExecutionDenied(f"Kernel message type {msg_type!r} is not allowed")

    def handle_incoming_message(self, incoming_msg) -> None:
        try:
            if len(incoming_msg) > MAX_MESSAGE_BYTES:
                raise ExecutionDenied("Kernel websocket frame is too large")
            if not self.channels:
                return

            if self.subprotocol == "v1.kernel.websocket.jupyter.org":
                channel, msg_list = deserialize_msg_from_ws_v1(incoming_msg)
                if len(msg_list) < 4:
                    raise ExecutionDenied("Malformed v1 kernel message")
                msg = {
                    "header": self.session.unpack(msg_list[0]),
                    "parent_header": self.session.unpack(msg_list[1]),
                    "metadata": self.session.unpack(msg_list[2]),
                    "content": self.session.unpack(msg_list[3]),
                    "buffers": msg_list[4:],
                }
                self._authorize_message(channel, msg)
                msg_list[3] = self.session.pack(msg["content"])
                stream = self.channels.get(channel)
                if stream is None:
                    raise ExecutionDenied("Unknown kernel channel")
                self.session.send_raw(stream, msg_list)
            else:
                if isinstance(incoming_msg, bytes):
                    msg = deserialize_binary_message(incoming_msg)
                else:
                    msg = json.loads(incoming_msg)
                channel = msg.pop("channel", "shell")
                self._authorize_message(channel, msg)
                stream = self.channels.get(channel)
                if stream is None:
                    raise ExecutionDenied("Unknown kernel channel")
                self.session.send(stream, msg)

            timeout_manager = getattr(self.websocket_handler.application, "_timeout_manager", None)
            if timeout_manager is not None:
                timeout_manager.touch()
        except (ExecutionDenied, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            self._deny(str(exc))
        except Exception:
            logger.exception("Kernel websocket policy failed closed")
            self._deny("Internal execution-policy failure")

    def handle_outgoing_message(self, stream, outgoing_msg) -> None:
        # Observe kernel-created comms without deserializing through Session twice.
        try:
            _, fed_msg_list = self.session.feed_identities(outgoing_msg)
            if len(fed_msg_list) >= 5:
                header = self.session.unpack(fed_msg_list[1])
                parent_header = self.session.unpack(fed_msg_list[2])
                metadata = self.session.unpack(fed_msg_list[3])
                content = self.session.unpack(fed_msg_list[4])
                msg_type = header.get("msg_type")
                comm_id = content.get("comm_id") if isinstance(content, Mapping) else None
                if isinstance(comm_id, str):
                    if msg_type == "comm_open":
                        self._mercury_record.comm_ids.add(comm_id)
                    elif msg_type == "comm_close":
                        self._mercury_record.comm_ids.discard(comm_id)
                coordinator = getattr(self, "_shared_session_coordinator", None)
                if coordinator is not None:
                    coordinator.observe_kernel_message(
                        self._mercury_record.session_id,
                        {
                            "header": header,
                            "parent_header": parent_header,
                            "metadata": metadata,
                            "content": content,
                        },
                    )
        except Exception:
            logger.exception("Failed to observe outgoing kernel comm lifecycle")
        return super().handle_outgoing_message(stream, outgoing_msg)
