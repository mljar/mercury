import logging
import os
import subprocess
import sys
import requests

from celery import shared_task
from django.conf import settings

from apps.workers.models import Worker
from apps.ws.utils import machine_uuid

from apps.workers.utils import get_running_machines, shuffle_machines, need_instance


log = logging.getLogger(__name__)


@shared_task(bind=True)
def task_start_websocket_worker(self, job_params):
    log.debug(f"NbWorkers per machine: {settings.NBWORKERS_PER_MACHINE}")

    if os.environ.get("MACHINE_SPELL", "") == "":
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
        machines = get_running_machines()
        machines = shuffle_machines(machines)

        workers_ips = [m.ipv4 for m in machines]

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
            need_instance(job_params["worker_id"])
            task_start_websocket_worker.s(job_params).apply_async(countdown=15)
