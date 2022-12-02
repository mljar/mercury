from cgitb import text
import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from apps.executor.models import Worker
from apps.notebooks.models import Notebook

WORKER_SITE = "worker"
CLIENT_SITE = "client"

class WorkerProxy(WebsocketConsumer):
    def connect(self):
        self.notebook_id = int(self.scope["url_route"]["kwargs"]["notebook_id"])
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]
        self.site = self.scope["url_route"]["kwargs"]["site"]
        
        print(f"Connect {self.site} to {self.session_id}, notebook id {self.notebook_id}")

        self.is_worker = self.site == WORKER_SITE
        self.is_client = self.site != WORKER_SITE

        self.client_group = f"group-{self.session_id}-{CLIENT_SITE}"
        self.worker_group = f"group-{self.session_id}-{WORKER_SITE}"
        
        self.group = self.worker_group if self.is_worker else self.client_group

        if self.is_client:
            # check for worker
            workers = Worker.objects.filter(session_id = self.session_id)

            if not workers:
                print("Create worker in db")
                #notebook = Notebook.objects.get(pk=2)
                worker = Worker(session_id = self.session_id, notebook_id=self.notebook_id, state="create")
                worker.save()
        
        should_accept = True
        if self.is_worker:
            workers = Worker.objects.filter(session_id = self.session_id)
            if len(workers) > 1:
                should_accept = False


        if should_accept:
            async_to_sync(self.channel_layer.group_add)(
                self.group, self.channel_name
            )

            self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.group, self.channel_name
        )

    def receive(self, text_data):
        print(f"Received from {self.site}:", text_data)

        json_data = json.loads(text_data)

        if self.is_client:
            # send to all clients
            async_to_sync(self.channel_layer.group_send)(
                self.client_group, {"type": "broadcast_message", "payload": json_data}
            )
            # sent to worker (should be only one)
            async_to_sync(self.channel_layer.group_send)(
                self.worker_group, {"type": "broadcast_message", "payload": json_data}
            )

        if self.is_worker:
            # send to all clients
            async_to_sync(self.channel_layer.group_send)(
                self.client_group, {"type": "broadcast_message", "payload": json_data}
            )

    def broadcast_message(self, event):
        payload = event["payload"]
        self.send(text_data=json.dumps({"payload": payload}))
