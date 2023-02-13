from enum import Enum
import threading

stop_event = threading.Event()


class WorkerState(str, Enum):
    Busy = "Busy"
    Running = "Running"
    Unknown = "Unknown"


class Purpose(str, Enum):
    WorkerPing = "worker-ping"
    WorkerState = "worker-state"
    InitNotebook = "init-notebook"
    RunNotebook = "run-notebook"
    SaveNotebook = "save-notebook"
    SavedNotebook = "saved-notebook"
    DisplayNotebook = "display-notebook"
    ClearSession = "clear-session"
    CloseWorker = "close-worker"

    ExecutedNotebook = "executed-notebook"
    UpdateWidgets = "update-widgets"
    HideWidgets = "hide-widgets"
    InitWidgets = "init-widgets"
    UpdateTitle = "update-title"
    UpdateShowCode = "update-show-code"

    DownloadHTML = "download-html"
    DownloadPDF = "download-pdf"
