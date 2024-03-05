import os
import json
import logging

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from apps.workers.models import Worker, WorkerSession
from apps.workers.constants import WorkerSessionState
from apps.ws.utils import client_group, worker_group

logging.basicConfig(
    format="WORKER %(asctime)s %(message)s",
    level=os.getenv("DJANGO_LOG_LEVEL", "ERROR"),
)

log = logging.getLogger(__name__)


class WorkerProxy(WebsocketConsumer):
    def connect(self):
        self.notebook_id = int(self.scope["url_route"]["kwargs"]["notebook_id"])
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]
        self.worker_id = self.scope["url_route"]["kwargs"]["worker_id"]

        # check if there is such worker requested in database
        workers = Worker.objects.filter(
            pk=self.worker_id, notebook__id=self.notebook_id, session_id=self.session_id
        )
        if not workers:
            self.close()

        log.info(
            f"Worker ({self.worker_id}) connect to {self.session_id}, notebook id {self.notebook_id}"
        )

        self.client_group = client_group(self.notebook_id, self.session_id)
        self.worker_group = worker_group(self.notebook_id, self.session_id)

        async_to_sync(self.channel_layer.group_add)(
            self.worker_group, self.channel_name
        )

        worker = workers[len(workers) - 1]
        self.worker_session = WorkerSession.objects.create(
            ipv4="unknown",
            state=WorkerSessionState.Running,
            owned_by=worker.notebook.created_by,
            run_by=worker.run_by,
            site=worker.notebook.hosted_on,
            notebook=worker.notebook,
            worker=worker,
        )

        self.accept()

    def disconnect(self, close_code):
        self.worker_session.sate = WorkerSessionState.Stopped
        self.worker_session.worker = None
        self.worker_session.save()
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
