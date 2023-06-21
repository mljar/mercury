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