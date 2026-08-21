import logging
from collections.abc import Mapping
from threading import Event as ThreadEvent, RLock, Thread
from time import sleep

from .process import InProcessWorker, MultiprocessWorker
from .protocol import ControlMessage, KINDS, TaskCommand, TaskEvent
from .registry import make_registry
from .slot import WorkerSlot


class WorkerSupervisor:
    def __init__(self, handlers: Mapping[str, object] | None = None, *, use_processes=True, poll_interval=0.05, event_callback=None):
        self.registry = make_registry(handlers)
        self.use_processes = use_processes
        self.poll_interval = poll_interval
        self.slots = {kind: WorkerSlot(kind) for kind in KINDS}
        self._events = __import__("queue").Queue()
        self._states = {}
        self._lock = RLock()
        self._event_callback = event_callback
        self._monitor_stop = ThreadEvent()
        self._monitor = None

    def set_event_callback(self, callback):
        self._event_callback = callback

    def start(self):
        for slot in self.slots.values():
            self._start_slot(slot)
        if self._event_callback is not None and self._monitor is None:
            self._monitor_stop.clear()
            self._monitor = Thread(target=self._monitor_events, daemon=True)
            self._monitor.start()

    def _monitor_events(self):
        while not self._monitor_stop.is_set():
            self.poll_events()
            self._monitor_stop.wait(self.poll_interval)

    def _start_slot(self, slot):
        slot.generation += 1
        slot.state = "idle"
        worker_type = MultiprocessWorker if self.use_processes else InProcessWorker
        slot.process = worker_type(slot.kind, self.registry, self._events.put)

    def submit(self, command: TaskCommand):
        slot = self.slots[command.kind]
        with self._lock:
            self._states[command.task_id] = "queued"
            slot.enqueue(command)
            self._dispatch(slot)

    def _dispatch(self, slot):
        if slot.active_task_id is not None or slot.state != "idle":
            return
        try:
            command = slot.queue.get_nowait()
        except Exception:
            return
        if self._states.get(command.task_id) == "cancelled":
            return self._dispatch(slot)
        slot.active_task_id = command.task_id
        slot.task_states[command.task_id] = "running"
        self._states[command.task_id] = "running"
        slot.state = "busy"
        slot.process.send(command)

    def poll_events(self):
        events = []
        while True:
            try:
                event = self._events.get_nowait()
            except __import__("queue").Empty:
                break
            if not isinstance(event, TaskEvent):
                continue
            slot = self.slots[event.kind]
            if slot.active_task_id != event.task_id:
                continue
            self._states[event.task_id] = "failed" if event.type == "failed" else (
                "succeeded" if event.type == "succeeded" else "running"
            )
            events.append(event)
            if self._event_callback is not None:
                try:
                    self._event_callback(event)
                except Exception:
                    logging.getLogger(__name__).exception("worker event callback failed")
            if event.type in ("succeeded", "failed"):
                slot.task_states[event.task_id] = self._states[event.task_id]
                slot.active_task_id, slot.state = None, "idle"
                if event.type == "failed":
                    self.restart(event.kind, reason="handler_failed")
                self._dispatch(slot)
        return events

    def send_control(self, message: ControlMessage, kind: str):
        slot = self.slots[kind]
        if message.type == "cancel" and message.task_id != slot.active_task_id:
            return False
        if slot.process is not None:
            slot.process.send(message)
        return True

    def cancel(self, task_id: str, kind: str):
        slot = self.slots[kind]
        if slot.active_task_id == task_id:
            self._states[task_id] = "cancelling"
            return self.send_control(ControlMessage(task_id, "cancel"), kind)
        if self._states.get(task_id) == "queued":
            self._states[task_id] = "cancelled"
            slot.task_states[task_id] = "cancelled"
            return True
        return False

    def restart(self, kind: str, reason="unknown"):
        slot = self.slots[kind]
        if slot.process is not None:
            slot.process.terminate()
        slot.process = None
        slot.active_task_id, slot.state = None, "dead"
        self._start_slot(slot)

    def task_state(self, task_id):
        return self._states.get(task_id)

    def queued_task_ids(self, kind):
        return self.slots[kind].queued_task_ids()

    def shutdown(self):
        self._monitor_stop.set()
        if self._monitor is not None:
            self._monitor.join(timeout=1)
            self._monitor = None
        for slot in self.slots.values():
            if slot.process is not None:
                slot.process.send(ControlMessage(None, "shutdown"))
                slot.process.terminate()
                slot.process = None
