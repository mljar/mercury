import json
from cgitb import text

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.db import transaction

from apps.ws.utils import get_client_group, get_worker_group
from apps.ws.models import Worker
from apps.ws.tasks import task_start_websocket_worker
from apps.notebooks.models import Notebook


class WorkerProxy(WebsocketConsumer):
    def connect(self):
        self.notebook_id = int(self.scope["url_route"]["kwargs"]["notebook_id"])
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]
        self.worker_id = self.scope["url_route"]["kwargs"]["worker_id"]

        print(
            f"Worker ({self.worker_id}) connect to {self.session_id}, notebook id {self.notebook_id}"
        )

        self.client_group = get_client_group(self.notebook_id, self.session_id)
        self.worker_group = get_worker_group(self.notebook_id, self.session_id)

        print("worker add", self.worker_group)

        async_to_sync(self.channel_layer.group_add)(
            self.worker_group, self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.worker_group, self.channel_name
        )

    def receive(self, text_data):
        # print(f"Worker ({self.worker_id}) received:", text_data)

        json_data = json.loads(text_data)

        # send to all clients
        async_to_sync(self.channel_layer.group_send)(
            self.client_group, {"type": "broadcast_message", "payload": json_data}
        )

    def broadcast_message(self, event):
        payload = event["payload"]
        self.send(text_data=json.dumps(payload))
