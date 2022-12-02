from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/client/(?P<session_id>.+)/(?P<notebook_id>.+)/$", consumers.ClientProxy.as_asgi()),
    re_path(r"ws/worker/(?P<session_id>.+)/(?P<notebook_id>.+)/(?P<worker_id>.+)/$", consumers.ExecutorProxy.as_asgi()),
]
