from django.urls import re_path

from .consumers.client import ClientProxy
from .consumers.worker import WorkerProxy

websocket_urlpatterns = [
    re_path(
        r"ws/client/(?P<notebook_id>.+)/(?P<session_id>.+)/$",
        ClientProxy.as_asgi(),
    ),
    re_path(
        r"ws/worker/(?P<notebook_id>.+)/(?P<session_id>.+)/(?P<worker_id>.+)/$",
        WorkerProxy.as_asgi(),
    ),
]
