from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(
        r"ws/client/(?P<notebook_id>.+)/(?P<session_id>.+)/$",
        consumers.ClientProxy.as_asgi(),
    ),
    re_path(
        r"ws/worker/(?P<notebook_id>.+)/(?P<session_id>.+)/(?P<worker_id>.+)/$",
        consumers.WorkerProxy.as_asgi(),
    ),
]
