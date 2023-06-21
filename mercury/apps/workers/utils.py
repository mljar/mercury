import random
from datetime import timedelta
from django.utils import timezone

from apps.workers.models import Machine, MachineState


def get_running_machines():
    machines = Machine.objects.filter(
        state=MachineState.Running,
        updated_at__gte=timezone.now() - timedelta(seconds=30),
    )
    return machines

def shuffle_machines(machines):
    machines = list(machines)
    random.shuffle(machines)
    return machines

def start_new_machine():
    pass

def start_sleeping_machine():
    pass

def terminate_machine():
    pass

def hibernate_machine():
    pass