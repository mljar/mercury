import os
import subprocess
import sys
import logging

from celery import shared_task

log = logging.getLogger(__name__)

@shared_task(bind=True)
def task_start_websocket_worker(self, job_params):
    command = [
        sys.executable,
        os.path.join("apps", "nbworker"),
        str(job_params["notebook_id"]),
        str(job_params["session_id"]),
        str(job_params["worker_id"]),
    ]
    log.debug("Start " + " ".join(command))
    worker = subprocess.Popen(command)
    
