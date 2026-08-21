import time

import pytest

from backend.workers.handlers.base import TaskHandler, TaskResult
from backend.workers.protocol import ControlMessage, TaskCommand
from backend.workers.protocol import EVENT_TYPES
from backend.workers.supervisor import WorkerSupervisor


KINDS = ("enhancement", "training", "dataset_download")


class FakeHandler(TaskHandler):
    def run(self, payload, context):
        if payload.get("fail"):
            raise RuntimeError("fake failure")
        for _ in range(payload.get("steps", 1)):
            if context.cancel_event.is_set():
                raise InterruptedError("cancelled")
            time.sleep(payload.get("delay", 0.01))
        return TaskResult(value={"task": context.task_id})


@pytest.fixture
def supervisor():
    worker = WorkerSupervisor(
        handlers={kind: FakeHandler for kind in KINDS},
        use_processes=False,
        poll_interval=0.005,
    )
    worker.start()
    yield worker
    worker.shutdown()


def command(task_id, kind, **payload):
    return TaskCommand(task_id=task_id, kind=kind, payload=payload)


def events_until(worker, count, timeout=2):
    deadline = time.monotonic() + timeout
    events = []
    while len(events) < count and time.monotonic() < deadline:
        events.extend(worker.poll_events())
        time.sleep(0.005)
    return events


def test_starts_three_fixed_slots(supervisor):
    assert set(supervisor.slots) == set(KINDS)
    assert all(slot.state == "idle" for slot in supervisor.slots.values())


def test_one_active_task_per_kind_and_same_kind_tasks_queue(supervisor):
    supervisor.submit(command("e1", "enhancement", steps=4, delay=0.02))
    supervisor.submit(command("e2", "enhancement"))
    time.sleep(0.02)
    assert supervisor.slots["enhancement"].active_task_id == "e1"
    assert supervisor.queued_task_ids("enhancement") == ["e2"]
    events = events_until(supervisor, 4)
    assert [event.type for event in events if event.kind == "enhancement"] == [
        "started",
        "succeeded",
        "started",
        "succeeded",
    ]


def test_different_kinds_run_in_parallel(supervisor):
    started = time.monotonic()
    for kind in KINDS:
        supervisor.submit(command(kind + "-1", kind, steps=4, delay=0.03))
    events = events_until(supervisor, 6)
    assert {event.task_id for event in events if event.type == "started"} == {
        kind + "-1" for kind in KINDS
    }
    assert time.monotonic() - started < 0.35


def test_command_event_control_protocol_and_task_matching(supervisor):
    supervisor.submit(command("right", "training"))
    supervisor.send_control(ControlMessage(task_id="wrong", type="cancel"), "training")
    events = events_until(supervisor, 2)
    assert [(event.task_id, event.kind, event.type) for event in events] == [
        ("right", "training", "started"),
        ("right", "training", "succeeded"),
    ]


def test_cancel_queued_and_running_tasks(supervisor):
    supervisor.submit(command("running", "dataset_download", steps=20, delay=0.02))
    supervisor.submit(command("queued", "dataset_download"))
    assert supervisor.cancel("queued", "dataset_download") is True
    assert supervisor.cancel("running", "dataset_download") is True
    events = events_until(supervisor, 2)
    assert {event.type for event in events} == {"started", "failed"}
    assert supervisor.task_state("queued") == "cancelled"


def test_failed_slot_is_restarted_without_affecting_other_slots(supervisor):
    supervisor.submit(command("bad", "enhancement", fail=True))
    assert events_until(supervisor, 2)[-1].type == "failed"
    old_generation = supervisor.slots["enhancement"].generation
    supervisor.restart("enhancement", reason="test")
    assert supervisor.slots["enhancement"].generation > old_generation
    supervisor.submit(command("good", "training"))
    assert events_until(supervisor, 2)[-1].type == "succeeded"


def test_protocol_and_slot_do_not_persist_process_runtime_leases():
    command_fields = set(TaskCommand.__dataclass_fields__)
    assert command_fields == {"task_id", "kind", "payload", "storage_paths"}
    assert not {"pid", "pgid", "token", "runtime_lease"}.intersection(command_fields)
    assert "progress" not in EVENT_TYPES
