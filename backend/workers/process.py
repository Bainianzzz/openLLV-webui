import logging
import multiprocessing as mp
from queue import Empty
from threading import Event, Thread

from .context import WorkerContext
from .protocol import ControlMessage, TaskCommand, TaskEvent
from .registry import get_handler


def execute_command(command: TaskCommand, kind, registry, emit, controls, stop: Event):
    handler = get_handler(registry, kind)
    context = WorkerContext(command.task_id, kind, {key: value for key, value in command.storage_paths.items()})
    control_done = Event()

    def watch_controls():
        while not control_done.is_set() and not stop.is_set():
            try:
                control = controls.get(timeout=0.02)
            except Empty:
                continue
            if control.type == "cancel" and control.task_id == command.task_id:
                context.cancel_event.set()

    watcher = Thread(target=watch_controls, daemon=True)
    watcher.start()
    emit(TaskEvent(command.task_id, kind, "started"))
    try:
        handler.validate(command.payload)
        outcome = handler.run(command.payload, context)
        if context.cancel_event.is_set():
            raise InterruptedError("cancelled")
        emit(TaskEvent(command.task_id, kind, "succeeded", handler.build_result(outcome, context)))
    except BaseException as exc:
        emit(TaskEvent(command.task_id, kind, "failed", {
            "error_code": "cancelled" if isinstance(exc, InterruptedError) else "handler_error",
            "safe_message": str(exc),
            "retryable": not isinstance(exc, InterruptedError),
        }))
    finally:
        control_done.set()
        try:
            handler.cleanup(context)
        except Exception:
            logging.getLogger(__name__).exception("handler cleanup failed")


def worker_main(kind, command_pipe, event_pipe, registry):
    stop = Event()
    controls = __import__("queue").Queue()
    task_thread = None

    def emit(event):
        event_pipe.send(event)

    while not stop.is_set():
        if task_thread is not None and not task_thread.is_alive():
            task_thread = None
        if command_pipe.poll(0.05):
            message = command_pipe.recv()
            if isinstance(message, ControlMessage):
                if message.type == "shutdown":
                    stop.set()
                else:
                    controls.put(message)
                continue
            if isinstance(message, TaskCommand) and task_thread is None:
                task_thread = Thread(
                    target=execute_command,
                    args=(message, kind, registry, emit, controls, stop),
                    daemon=True,
                )
                task_thread.start()


class MultiprocessWorker:
    def __init__(self, kind, registry, emit):
        context = mp.get_context("spawn")
        parent_pipe, child_pipe = context.Pipe(duplex=False)
        parent_events, child_events = context.Pipe(duplex=False)
        self.pipe = child_pipe
        self.process = context.Process(target=worker_main, args=(kind, parent_pipe, child_events, registry))
        self.process.start()
        self._reader = Thread(target=self._read_events, args=(parent_events, emit), daemon=True)
        self._reader.start()

    def _read_events(self, pipe, emit):
        try:
            while True:
                emit(pipe.recv())
        except (EOFError, OSError):
            return

    def send(self, message):
        self.pipe.send(message)

    def terminate(self):
        if self.process.is_alive():
            self.process.terminate()
        self.process.join(timeout=1)

    def join(self, timeout=None):
        self.process.join(timeout)


class InProcessWorker:
    def __init__(self, kind, registry, emit):
        self.kind, self.registry, self.emit = kind, registry, emit
        self.commands, self.controls = __import__("queue").Queue(), __import__("queue").Queue()
        self.stop = Event()
        self.thread = Thread(target=self._run, name=f"worker-{kind}", daemon=True)
        self.thread.start()

    def _run(self):
        while not self.stop.is_set():
            try:
                message = self.commands.get(timeout=0.05)
            except Empty:
                continue
            if isinstance(message, ControlMessage):
                if message.type == "shutdown":
                    self.stop.set()
                else:
                    self.controls.put(message)
                continue
            execute_command(message, self.kind, self.registry, self.emit, self.controls, self.stop)

    def send(self, message):
        if isinstance(message, ControlMessage) and message.type == "cancel":
            self.controls.put(message)
        else:
            self.commands.put(message)

    def terminate(self):
        self.stop.set()
        self.thread.join(timeout=1)

    def join(self, timeout=None):
        self.thread.join(timeout)
