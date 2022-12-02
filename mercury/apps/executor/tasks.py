import os
import sys
import subprocess

from celery import shared_task


@shared_task(bind=True)
def task_start_websocket_worker(self, job_params):

    command = [
        sys.executable,
        os.path.join("apps", "executor", "worker.py"),
        job_params["notebook_id"],
        job_params["session_id"],
        job_params["worker_id"],
    ]
    print(command)
    # worker = subprocess.Popen(command)
    print("end")
