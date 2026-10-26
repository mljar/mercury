from types import SimpleNamespace

import pytest

from mercury_app.execution.connection import (
    MAX_MESSAGE_BYTES,
    MercuryKernelWebsocketConnection,
)
from mercury_app.execution.manifest import NotebookExecutionManifest
from mercury_app.execution.policy import ExecutionDenied
from mercury_app.execution.shared_session import SharedSessionCoordinator


def connection():
    value = object.__new__(MercuryKernelWebsocketConnection)
    value._mercury_record = SimpleNamespace(
        manifest=NotebookExecutionManifest.from_notebook(
            "app.ipynb",
            {"cells": [{"id": "safe", "cell_type": "code", "source": "print('safe')"}]},
        ),
        comm_ids=set(),
        comm_policies={},
        session_id="session",
    )
    return value


class SharedClient:
    client_id = "client"

    def send_shared_session_message(self, message):
        self.last_message = message


def message(msg_type, *, metadata=None, content=None, buffers=None):
    return {
        "header": {"msg_type": msg_type},
        "metadata": metadata or {},
        "content": content or {},
        "buffers": buffers or [],
    }


def test_execute_request_replaces_code_and_user_expressions():
    value = message(
        "execute_request",
        metadata={"cellId": "safe"},
        content={
            "code": "__import__('os').system('id')",
            "allow_stdin": True,
            "user_expressions": {"attack": "__import__('os').getcwd()"},
        },
    )
    connection()._authorize_message("shell", value)
    assert value["content"]["code"] == "print('safe')"
    assert value["content"]["allow_stdin"] is False
    assert value["content"]["user_expressions"] == {}


def test_shared_cell_execution_requires_the_active_run_lease():
    value = connection()
    coordinator = SharedSessionCoordinator()
    client = SharedClient()
    coordinator.join(
        session_id="session", kernel_id="kernel", cell_count=1, client=client
    )
    run = client.last_message
    # The busy broadcast follows the targeted run message.
    if run["type"] == "busy":
        run = value_run = coordinator.room("session").active_run
        run_id, token = value_run.run_id, value_run.token
    else:
        run_id, token = run["run_id"], run["token"]
    value._shared_session_coordinator = coordinator

    with pytest.raises(ExecutionDenied, match="run lease"):
        value._authorize_message(
            "shell",
            message(
                "execute_request",
                metadata={"mercury": {"kind": "cell", "cell_id": "safe"}},
            ),
        )

    authorized = message(
        "execute_request",
        metadata={
            "mercury": {
                "kind": "cell",
                "cell_id": "safe",
                "shared_session": {
                    "client_id": "client",
                    "run_id": run_id,
                    "token": token,
                },
            }
        },
    )
    authorized["header"]["msg_id"] = "request"
    value._authorize_message("shell", authorized)


@pytest.mark.parametrize(
    "msg_type",
    ["debug_request", "shutdown_request", "complete_request", "input_reply"],
)
def test_dangerous_or_unneeded_kernel_messages_are_rejected(msg_type):
    with pytest.raises(ExecutionDenied):
        connection()._authorize_message("shell", message(msg_type))


def test_comm_messages_require_a_kernel_registered_comm_id():
    value = connection()
    with pytest.raises(ExecutionDenied):
        value._authorize_message(
            "shell", message("comm_msg", content={"comm_id": "unknown", "data": {}})
        )

    value._mercury_record.comm_ids.add("known")
    value._authorize_message(
        "shell",
        message(
            "comm_msg",
            content={"comm_id": "known", "data": {"method": "request_state"}},
        ),
    )


def test_only_standard_widget_control_comm_can_be_browser_created():
    value = connection()
    value._authorize_message(
        "shell",
        message(
            "comm_open",
            content={"comm_id": "control", "target_name": "jupyter.widget.control"},
        ),
    )
    assert "control" in value._mercury_record.comm_ids

    with pytest.raises(ExecutionDenied):
        value._authorize_message(
            "shell",
            message(
                "comm_open",
                content={"comm_id": "custom", "target_name": "dangerous.custom.target"},
            ),
        )


class SizedBuffer:
    def __init__(self, size):
        self.size = size

    def __len__(self):
        return self.size


def test_widget_buffers_support_upload_limit_but_reject_larger_payloads():
    value = connection()
    value._mercury_record.comm_ids.add("upload")
    value._observe_comm(
        "comm_open",
        {
            "comm_id": "upload",
            "data": {
                "state": {
                    "_model_module": "anywidget",
                    "_anywidget_id": "mercury.file.UploadFileWidget",
                }
            },
        },
    )
    value._authorize_message(
        "shell",
        message(
            "comm_msg",
            content={
                "comm_id": "upload",
                "data": {"method": "custom", "content": {"event": "upload_files"}},
            },
            buffers=[SizedBuffer(100 * 1024 * 1024)],
        ),
    )
    with pytest.raises(ExecutionDenied, match="too large"):
        value._authorize_message(
            "shell",
            message(
                "comm_msg",
                content={"comm_id": "upload", "data": {}},
                buffers=[SizedBuffer(MAX_MESSAGE_BYTES + 1)],
            ),
        )


def test_kernel_widget_identity_controls_which_fields_the_browser_can_update():
    value = connection()
    value._observe_comm(
        "comm_open",
        {
            "comm_id": "widget",
            "data": {
                "state": {
                    "_model_module": "anywidget",
                    "_anywidget_id": "mercury.text.TextInputWidget",
                }
            },
        },
    )

    def update(state):
        return message(
            "comm_msg",
            content={
                "comm_id": "widget",
                "data": {"method": "update", "state": state},
            },
        )

    value._authorize_message("shell", update({"value": "hello"}))
    for field in ("_esm", "label", "_anywidget_id"):
        with pytest.raises(ExecutionDenied):
            value._authorize_message("shell", update({field: "untrusted"}))
    with pytest.raises(ExecutionDenied, match="already registered"):
        value._authorize_message(
            "shell",
            message(
                "comm_open",
                content={
                    "comm_id": "widget",
                    "target_name": "jupyter.widget.control",
                },
            ),
        )
    value._observe_comm("comm_close", {"comm_id": "widget"})
    assert "widget" not in value._mercury_record.comm_ids
    assert "widget" not in value._comm_policies


def test_control_snapshot_recovers_policies_for_existing_widgets():
    value = connection()
    value._authorize_message(
        "shell",
        message(
            "comm_open",
            content={
                "comm_id": "control",
                "target_name": "jupyter.widget.control",
            },
        ),
    )
    value._observe_comm(
        "comm_msg",
        {
            "comm_id": "control",
            "data": {
                "method": "update_states",
                "states": {
                    "output": {
                        "state": {
                            "_model_module": "@jupyter-widgets/controls",
                            "_model_name": "HTMLModel",
                        }
                    }
                },
            },
        },
    )
    assert "output" in value._mercury_record.comm_ids
    with pytest.raises(ExecutionDenied):
        value._authorize_message(
            "shell",
            message(
                "comm_msg",
                content={
                    "comm_id": "output",
                    "data": {
                        "method": "update",
                        "state": {"value": "<script>attack()</script>"},
                    },
                },
            ),
        )
