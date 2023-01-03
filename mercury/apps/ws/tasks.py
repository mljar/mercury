import os
import subprocess
import sys
import uuid
import logging

from celery import shared_task

from django.conf import settings

from apps.ws.models import Worker

log = logging.getLogger(__name__)

@shared_task(bind=True)
def task_start_websocket_worker(self, job_params):

    log.debug(f"NbWorkers per machine: {settings.NBWORKERS_PER_MACHINE}")
    machine_id = str(uuid.getnode())
    workers = Worker.objects.filter(machine_id=machine_id)

    log.debug(f"Workers count: {len(workers)} machine_id={ machine_id }")

    if len(workers) > settings.NBWORKERS_PER_MACHINE:
        log.debug("Defer task start ws worker")
        task_start_websocket_worker.s(job_params).apply_async(countdown=15)
    else:
        command = [
            sys.executable,
            os.path.join("apps", "nbworker"),
            str(job_params["notebook_id"]),
            str(job_params["session_id"]),
            str(job_params["worker_id"]),
        ]
        log.debug("Start " + " ".join(command))
        worker = subprocess.Popen(command)
    
