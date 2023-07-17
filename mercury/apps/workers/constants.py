from enum import Enum


class WorkerState(str, Enum):
    Busy = "Busy"
    Running = "Running"
    Unknown = "Unknown"
    MaxRunTimeReached = "MaxRunTimeReached"
    MaxIdleTimeReached = "MaxIdleTimeReached"
    InstallPackages = "InstallPackages"


class MachineState(str, Enum):
    Pending = "Pending"
    Running = "Running"
    Stopping = "Stopping"
    Stopped = "Stopped"
    ShuttingDown = "ShuttingDown"
    Terminated = "Terminated"


class WorkerSessionState(str, Enum):
    Running = "Running"
    Stopped = "Stopped"
