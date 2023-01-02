import json
from cgitb import text
from datetime import datetime, timedelta

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.db import transaction
from django.db.models import Q
from django.utils.timezone import make_aware

from apps.ws.utils import get_client_group, get_worker_group
from apps.ws.models import Worker
from apps.ws.tasks import task_start_websocket_worker
from apps.notebooks.models import Notebook


class ClientProxy(WebsocketConsumer):
    def connect(self):
        self.notebook_id = int(self.scope["url_route"]["kwargs"]["notebook_id"])
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]

        print(f"Client connect to {self.notebook_id}/{self.session_id}")

        self.client_group = get_client_group(self.notebook_id, self.session_id)
        self.worker_group = get_worker_group(self.notebook_id, self.session_id)

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
        print(f"Client received:", text_data)

        json_data = json.loads(text_data)

        if "purpose" in json_data:
            if json_data["purpose"] == "worker-ping":
                self.worker_ping()
                return
            if json_data["purpose"] == "run-notebook":
                async_to_sync(self.channel_layer.group_send)(
                    self.worker_group,
                    {"type": "broadcast_message", "payload": json_data},
                )
        # send to all clients
        # async_to_sync(self.channel_layer.group_send)(
        #    self.client_group, {"type": "broadcast_message", "payload": json_data}
        # )

    def broadcast_message(self, event):
        print("client broadcast")
        payload = event["payload"]
        self.send(text_data=json.dumps(payload))

    def need_worker(self):
        with transaction.atomic():
            print("Create worker in db")
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

        # clearn stale workers
        workers = Worker.objects.filter(
            updated_at__lte=make_aware(datetime.now() - timedelta(minutes=1))
        )
        workers.delete()
