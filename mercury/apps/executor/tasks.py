import os
import sys
import subprocess

from celery import shared_task


@shared_task(bind=True)
def task_start_websocket_worker(self, job_params):

    command = [
        sys.executable,
        os.path.join("apps", "executor", "worker.py"),
        str(job_params["notebook_id"]),
        str(job_params["session_id"]),
        str(job_params["worker_id"]),
    ]
    print(command)
    print(" ".join(command))
    # worker = subprocess.Popen(command)
    print("end")
