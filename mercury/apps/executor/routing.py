from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/execute/(?P<session_id>\w+)/$", consumers.ExecutorProxy.as_asgi()),
]