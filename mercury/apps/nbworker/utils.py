import threading
from enum import Enum

stop_event = threading.Event()


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
