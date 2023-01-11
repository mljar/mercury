import json
import logging

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from apps.ws.utils import client_group, worker_group

log = logging.getLogger(__name__)


class WorkerProxy(WebsocketConsumer):
    def connect(self):
        self.notebook_id = int(self.scope["url_route"]["kwargs"]["notebook_id"])
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]
        self.worker_id = self.scope["url_route"]["kwargs"]["worker_id"]

        log.debug(
            f"Worker ({self.worker_id}) connect to {self.session_id}, notebook id {self.notebook_id}"
        )

        self.client_group = client_group(self.notebook_id, self.session_id)
        self.worker_group = worker_group(self.notebook_id, self.session_id)

        async_to_sync(self.channel_layer.group_add)(
            self.worker_group, self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.worker_group, self.channel_name
        )

    def receive(self, text_data):
        json_data = json.loads(text_data)
        # broadcast to all clients
        async_to_sync(self.channel_layer.group_send)(
            self.client_group, {"type": "broadcast_message", "payload": json_data}
        )

    def broadcast_message(self, event):
        payload = event["payload"]
        self.send(text_data=json.dumps(payload))
