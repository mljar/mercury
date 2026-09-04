import asyncio

from mercury_app.execution.shared_session import (
    MAX_SNAPSHOT_EVENTS_PER_CELL,
    SharedSessionCoordinator,
)


class Client:
    def __init__(self, client_id):
        self.client_id = client_id
        self.messages = []

    def send_shared_session_message(self, message):
        self.messages.append(message)


def messages(client, message_type):
    return [m for m in client.messages if m["type"] == message_type]


def test_first_client_initializes_and_joiner_does_not_run_again():
    coordinator = SharedSessionCoordinator()
    first = Client("first")
    second = Client("second")

    coordinator.join(
        session_id="session", kernel_id="kernel", cell_count=8, client=first
    )
    initial = messages(first, "run")[-1]
    assert initial["initialize"] is True

    coordinator.complete_run(
        "session", "first", initial["run_id"], initial["token"]
    )
    coordinator.join(
        session_id="session", kernel_id="kernel", cell_count=8, client=second
    )

    assert messages(second, "welcome")[-1]["initialized"] is True
    assert messages(second, "run") == []


def test_requests_are_coalesced_to_earliest_cell():
    coordinator = SharedSessionCoordinator()
    first = Client("first")
    second = Client("second")
    coordinator.join(
        session_id="session", kernel_id="kernel", cell_count=10, client=first
    )
    initial = messages(first, "run")[-1]
    coordinator.join(
        session_id="session", kernel_id="kernel", cell_count=10, client=second
    )

    coordinator.request_run("session", "second", 7)
    coordinator.request_run("session", "first", 3)
    coordinator.complete_run(
        "session", "first", initial["run_id"], initial["token"]
    )

    follow_up = messages(first, "run")[-1]
    assert follow_up["initialize"] is False
    assert follow_up["from_index"] == 3


def test_recovery_run_prefers_another_connected_client():
    coordinator = SharedSessionCoordinator()
    healthy = Client("healthy")
    joining = Client("joining")
    coordinator.join(
        session_id="session", kernel_id="kernel", cell_count=5, client=healthy
    )
    initial = messages(healthy, "run")[-1]
    coordinator.complete_run(
        "session", "healthy", initial["run_id"], initial["token"]
    )
    coordinator.join(
        session_id="session", kernel_id="kernel", cell_count=5, client=joining
    )

    recovery = coordinator.request_run(
        "session", "joining", 0, prefer_other=True
    )

    assert recovery is not None
    assert recovery.client_id == "healthy"
    assert messages(healthy, "run")[-1]["from_index"] == 0
    assert messages(joining, "run") == []


def test_executor_disconnect_reassigns_the_run():
    coordinator = SharedSessionCoordinator()
    first = Client("first")
    second = Client("second")
    coordinator.join(
        session_id="session", kernel_id="kernel", cell_count=5, client=first
    )
    coordinator.join(
        session_id="session", kernel_id="kernel", cell_count=5, client=second
    )

    coordinator.leave("session", "first")

    replacement = messages(second, "run")[-1]
    assert replacement["initialize"] is True
    assert replacement["from_index"] == 0


def test_pending_run_resumes_when_a_client_rejoins():
    coordinator = SharedSessionCoordinator()
    first = Client("first")
    coordinator.join(
        session_id="session", kernel_id="kernel", cell_count=5, client=first
    )
    initial = messages(first, "run")[-1]
    coordinator.complete_run(
        "session", "first", initial["run_id"], initial["token"]
    )
    current = coordinator.request_run("session", "first", 3)
    assert current is not None
    coordinator.leave("session", "first")

    second = Client("second")
    coordinator.join(
        session_id="session", kernel_id="kernel", cell_count=5, client=second
    )

    resumed = messages(second, "run")[-1]
    assert resumed["from_index"] == 3


def test_stale_run_completion_is_rejected():
    coordinator = SharedSessionCoordinator()
    client = Client("client")
    coordinator.join(
        session_id="session", kernel_id="kernel", cell_count=2, client=client
    )

    try:
        coordinator.complete_run("session", "client", 99, "stale")
    except ValueError as exc:
        assert "Stale" in str(exc)
    else:
        raise AssertionError("stale completion should be rejected")


def test_kernel_outputs_are_trusted_snapshots_and_broadcast_once():
    coordinator = SharedSessionCoordinator()
    first = Client("first")
    second = Client("second")
    room = coordinator.join(
        session_id="session", kernel_id="kernel", cell_count=2, client=first
    )
    coordinator.join(
        session_id="session", kernel_id="kernel", cell_count=2, client=second
    )
    run = messages(first, "run")[-1]
    coordinator.register_execute(
        session_id="session",
        client_id="first",
        run_id=run["run_id"],
        token=run["token"],
        message_id="request-1",
        cell_id="cell-1",
    )
    output = {
        "header": {"msg_id": "output-1", "msg_type": "display_data"},
        "parent_header": {"msg_id": "request-1"},
        "metadata": {},
        "content": {"data": {"text/plain": "hello"}, "metadata": {}},
    }

    coordinator.observe_kernel_message("session", output)
    coordinator.observe_kernel_message("session", output)

    assert room.outputs["cell-1"] == [output]
    assert len(messages(second, "output")) == 1
    assert messages(second, "output")[0]["reset"] is True


def test_initialization_waiter_is_released_after_first_run():
    async def scenario():
        coordinator = SharedSessionCoordinator()
        client = Client("client")
        coordinator.join(
            session_id="session", kernel_id="kernel", cell_count=1, client=client
        )
        run = messages(client, "run")[-1]
        waiter = asyncio.create_task(
            coordinator.wait_until_initialized("session", timeout=1)
        )
        await asyncio.sleep(0)
        coordinator.complete_run(
            "session", "client", run["run_id"], run["token"]
        )
        assert await waiter is True

    asyncio.run(scenario())


def test_output_snapshot_is_bounded_per_cell():
    coordinator = SharedSessionCoordinator()
    client = Client("client")
    room = coordinator.join(
        session_id="session", kernel_id="kernel", cell_count=1, client=client
    )
    run = messages(client, "run")[-1]
    coordinator.register_execute(
        session_id="session",
        client_id="client",
        run_id=run["run_id"],
        token=run["token"],
        message_id="request-1",
        cell_id="cell-1",
    )

    for index in range(MAX_SNAPSHOT_EVENTS_PER_CELL + 1):
        coordinator.observe_kernel_message(
            "session",
            {
                "header": {"msg_id": f"output-{index}", "msg_type": "stream"},
                "parent_header": {"msg_id": "request-1"},
                "metadata": {},
                "content": {"name": "stdout", "text": str(index)},
            },
        )

    assert len(room.outputs["cell-1"]) == MAX_SNAPSHOT_EVENTS_PER_CELL
    assert room.outputs["cell-1"][0]["content"]["text"] == "1"
