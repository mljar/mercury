from enum import Enum


class WorkerState(str, Enum):
    Busy = "Busy"
    Running = "Running"
    Unknown = "Unknown"


class Purpose(str, Enum):
    WorkerPing = "worker-ping"
    WorkerState = "worker-state"
    RunNotebook = "run-notebook"
    ClearSession = "clear-session"
    CloseWorker = "close-worker"
