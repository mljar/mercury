from types import SimpleNamespace

import pytest

from mercury_app.execution.connection import (
    MAX_MESSAGE_BYTES,
    MercuryKernelWebsocketConnection,
)
from mercury_app.execution.manifest import NotebookExecutionManifest
from mercury_app.execution.policy import ExecutionDenied


def connection():
    value = object.__new__(MercuryKernelWebsocketConnection)
    value._mercury_record = SimpleNamespace(
        manifest=NotebookExecutionManifest.from_notebook(
            "app.ipynb",
            {"cells": [{"id": "safe", "cell_type": "code", "source": "print('safe')"}]},
        ),
        comm_ids=set(),
    )
    return value


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
        "shell", message("comm_msg", content={"comm_id": "known", "data": {"x": 1}})
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
    value._authorize_message(
        "shell",
        message(
            "comm_msg",
            content={"comm_id": "upload", "data": {}},
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
