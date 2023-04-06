import logging
import os
import subprocess
import sys
import requests

from celery import shared_task
from django.conf import settings

from apps.workers.models import Worker
from apps.ws.utils import machine_uuid

log = logging.getLogger(__name__)


@shared_task(bind=True)
def task_start_websocket_worker(self, job_params):
    log.debug(f"NbWorkers per machine: {settings.NBWORKERS_PER_MACHINE}")

    workers_ip_list = os.environ.get("WORKERS_IP_LIST", "")

    if workers_ip_list == "":
        machine_id = machine_uuid()
        workers = Worker.objects.filter(machine_id=machine_id)

        log.debug(f"Workers count: {len(workers)} machine_id={ machine_id }")

        if len(workers) > settings.NBWORKERS_PER_MACHINE:
            log.debug("Defer task start ws worker")
            task_start_websocket_worker.s(job_params).apply_async(countdown=15)
        else:
            directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            command = [
                sys.executable,
                os.path.join(directory, "nbworker"),
                str(job_params["notebook_id"]),
                str(job_params["session_id"]),
                str(job_params["worker_id"]),
                job_params["server_url"],
            ]
            log.debug("Start " + " ".join(command))
            worker = subprocess.Popen(command)
    else:
        workers_ips = workers_ip_list.split(",")
        print(workers_ips)

        all_busy = True

        for worker_ip in workers_ips:
            try:
                workers = Worker.objects.filter(machine_id=worker_ip)

                log.debug(f"Workers count: {len(workers)} machine_id={ worker_ip }")

                if len(workers) <= settings.NBWORKERS_PER_MACHINE:
                    notebook_id = job_params["notebook_id"]
                    session_id = job_params["session_id"]
                    worker_id = job_params["worker_id"]
                    response = requests.get(
                        f"http://{worker_ip}/start/{notebook_id}/{session_id}/{worker_id}"
                    )
                    if response.status_code == 200:
                        if response.json().get("msg", "") == "ok":
                            all_busy = False
                            break
            except Exception as e:
                pass

        if all_busy:
            log.debug("Defer task start ws worker")
            task_start_websocket_worker.s(job_params).apply_async(countdown=15)
