from cgitb import text
import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from apps.executor.models import Worker
from apps.notebooks.models import Notebook


from django.db import transaction

from apps.executor.tasks import task_start_websocket_worker

CLIENT_SITE = "client"
WORKER_SITE = "worker"


class ClientProxy(WebsocketConsumer):
    def need_worker(self):
        # need worker
        with transaction.atomic():
            print("Create worker in db")
            worker = Worker(
                session_id=self.session_id,
                notebook_id=self.notebook_id,
                state="Initialized",
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
            session_id=self.session_id, notebook_id=self.notebook_id #, state="running"
        )
        if not workers:
            self.need_worker()
            async_to_sync(self.channel_layer.group_send)(
                self.client_group,
                {
                    "type": "broadcast_message",
                    "payload": {"purpose": "worker-pong", "status": "Initialized"},
                },
            )

        else:
            print("broadcast", self.worker_group)
            # otherwise, forward message to worker
            async_to_sync(self.channel_layer.group_send)(
                self.worker_group,
                {
                    "type": "broadcast_message",
                    "payload": {"purpose": "worker-ping"},
                },
            )

    def connect(self):
        self.notebook_id = int(self.scope["url_route"]["kwargs"]["notebook_id"])
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]

        print(f"Client connect to {self.notebook_id}/{self.session_id}")

        self.client_group = f"{CLIENT_SITE}-{self.notebook_id}-{self.session_id}"
        self.worker_group = f"{WORKER_SITE}-{self.notebook_id}-{self.session_id}"

        self.group = self.client_group

        print("ADD", self.group)
        async_to_sync(self.channel_layer.group_add)(self.group, self.channel_name)

        self.need_worker()

        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(self.group, self.channel_name)

    def receive(self, text_data):
        print(f"Client received:", text_data)

        json_data = json.loads(text_data)

        if json_data["purpose"] == "worker-ping":
            self.worker_ping()
            return

        # send to all clients
        async_to_sync(self.channel_layer.group_send)(
            self.client_group, {"type": "broadcast_message", "payload": json_data}
        )
        # sent to worker (should be only one)
        async_to_sync(self.channel_layer.group_send)(
            self.worker_group, {"type": "broadcast_message", "payload": json_data}
        )

    def broadcast_message(self, event):
        print("???")
        payload = event["payload"]
        self.send(text_data=json.dumps({"payload": payload}))


class WorkerProxy(WebsocketConsumer):
    def connect(self):
        self.notebook_id = int(self.scope["url_route"]["kwargs"]["notebook_id"])
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]
        self.worker_id = self.scope["url_route"]["kwargs"]["worker_id"]

        print(
            f"Worker ({self.worker_id}) connect to {self.session_id}, notebook id {self.notebook_id}"
        )

        self.client_group = f"{CLIENT_SITE}-{self.notebook_id}-{self.session_id}"
        self.worker_group = f"{WORKER_SITE}-{self.notebook_id}-{self.session_id}"

        self.group = self.worker_group

        print("ADD", self.group)
        async_to_sync(self.channel_layer.group_add)(self.group, self.channel_name)

        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(self.group, self.channel_name)

    def receive(self, text_data):
        print(f"Worker ({self.worker_id}) received:", text_data)

        json_data = json.loads(text_data)

        # send to all clients
        async_to_sync(self.channel_layer.group_send)(
            self.client_group, {"type": "broadcast_message", "payload": json_data}
        )

    def broadcast_message(self, event):
        print("worker ???")
        payload = event["payload"]
        self.send(text_data=json.dumps({"payload": payload}))
