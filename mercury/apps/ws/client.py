import json
import logging
from datetime import datetime, timedelta

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.db import transaction
from django.db.models import Q
from django.utils.timezone import make_aware

from apps.ws.models import Worker
from apps.ws.tasks import task_start_websocket_worker
from apps.ws.utils import client_group, worker_group

log = logging.getLogger(__name__)


class ClientProxy(WebsocketConsumer):
    def connect(self):
        self.notebook_id = int(self.scope["url_route"]["kwargs"]["notebook_id"])
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]

        log.debug(f"Client connect to {self.notebook_id}/{self.session_id}")

        self.client_group = client_group(self.notebook_id, self.session_id)
        self.worker_group = worker_group(self.notebook_id, self.session_id)

        async_to_sync(self.channel_layer.group_add)(
            self.client_group, self.channel_name
        )

        self.need_worker()

        self.accept()

    def disconnect(self, close_code):
        #
        # close worker
        #
        async_to_sync(self.channel_layer.group_send)(
            self.worker_group,
            {"type": "broadcast_message", "payload": {"purpose": "close-worker"}},
        )

        async_to_sync(self.channel_layer.group_discard)(
            self.client_group, self.channel_name
        )

    def receive(self, text_data):
        log.debug(f"Received from client: {text_data}")

        json_data = json.loads(text_data)

        if json_data.get("purpose", "") == "worker-ping":
            self.worker_ping()

        elif json_data.get("purpose", "") == "run-notebook":
            async_to_sync(self.channel_layer.group_send)(
                self.worker_group,
                {"type": "broadcast_message", "payload": json_data},
            )
        elif json_data.get("purpose", "") in [
            "save-notebook",
            "display-notebook",
            "download-html",
            "download-pdf",
        ]:
            async_to_sync(self.channel_layer.group_send)(
                self.worker_group,
                {"type": "broadcast_message", "payload": json_data},
            )

    def broadcast_message(self, event):
        payload = event["payload"]
        self.send(text_data=json.dumps(payload))

    def need_worker(self):
        with transaction.atomic():
            log.debug("Create worker in db")
            worker = Worker(
                session_id=self.session_id,
                notebook_id=self.notebook_id,
                state="Queued",
            )
            worker.save()
            job_params = {
                "notebook_id": self.notebook_id,
                "session_id": self.session_id,
                "worker_id": worker.id,
                "server_url": "ws://127.0.0.1:8000",
            }
            transaction.on_commit(lambda: task_start_websocket_worker.delay(job_params))

    def worker_ping(self):

        workers = Worker.objects.filter(
            Q(state="Running") | Q(state="Queued") | Q(state="Busy"),
            session_id=self.session_id,
            notebook_id=self.notebook_id,
        )

        if not workers:
            self.need_worker()
        else:
            async_to_sync(self.channel_layer.group_send)(
                self.worker_group,
                {
                    "type": "broadcast_message",
                    "payload": {"purpose": "worker-ping"},
                },
            )

        if workers.filter(state="Queued"):
            async_to_sync(self.channel_layer.group_send)(
                self.client_group,
                {
                    "type": "broadcast_message",
                    "payload": {"purpose": "worker-state", "state": "Queued"},
                },
            )

        # clear stale workers
        workers = Worker.objects.filter(
            updated_at__lte=make_aware(datetime.now() - timedelta(minutes=1))
        )
        workers.delete()
