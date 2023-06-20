from enum import Enum

from django.db import models

from apps.notebooks.models import Notebook


class WorkerState(str, Enum):
    Busy = "Busy"
    Running = "Running"
    Unknown = "Unknown"
    MaxRunTimeReached = "MaxRunTimeReached"
    MaxIdleTimeReached = "MaxIdleTimeReached"
    InstallPackages = "InstallPackages"


class Worker(models.Model):
    """It is a task that is done by the worker"""

    # machine unique id
    machine_id = models.CharField(max_length=128, blank=True)

    # web browser session id
    session_id = models.CharField(max_length=128)

    # notebook
    notebook = models.ForeignKey(
        Notebook,
        on_delete=models.CASCADE,
    )

    state = models.CharField(max_length=128, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)


class MachineState(str, Enum):
    Pending = "Pending"
    Running = "Running"
    Stopping = "Stopping"
    Stopped = "Stopped"
    ShuttingDown = "ShuttingDown"
    Terminated = "Terminated"


class Machine(models.Model):
    # machine ip v4 address
    ipv4 = models.CharField(max_length=128, blank=True)

    # state from MachineState
    state = models.CharField(max_length=128, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)
