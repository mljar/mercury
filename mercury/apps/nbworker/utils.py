from enum import Enum


class WorkerState(str, Enum):
    Busy = "Busy"
    Running = "Running"
    Unknown = "Unknown"


class Purpose(str, Enum):
    WorkerPing = "worker-ping"
    WorkerState = "worker-state"
    InitNotebook = "init-notebook"
    RunNotebook = "run-notebook"
    ClearSession = "clear-session"
    CloseWorker = "close-worker"

    ExecutedNotebook = "executed-notebook"
    UpdateWidgets = "update-widgets"
    HideWidgets = "hide-widgets"
