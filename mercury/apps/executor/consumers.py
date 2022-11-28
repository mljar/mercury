import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer


class ExecutorProxy(WebsocketConsumer):
    def connect(self):
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]
        self.session_group = f"session_{self.session_id}"
        
        async_to_sync(self.channel_layer.group_add)(
            self.session_group, self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.session_group, self.channel_name
        )

    def receive(self, text_data):
        json_data = json.loads(text_data)
        
        async_to_sync(self.channel_layer.group_send)(
            self.session_group, {"type": "broadcast_message", "payload": json_data}
        )

    def broadcast_message(self, event):
        payload = event["payload"]

        # Send message to WebSocket
        self.send(text_data=json.dumps({"payload": payload}))
        