from django.conf.urls import url

from apps.workers.views import (
    WorkerGetNb,
    GetWorker,
    SetWorkerState,
    DeleteWorker
)

workers_urlpatterns = [
    url(
        "api/v1/worker/(?P<session_id>.+)/(?P<worker_id>.+)/(?P<notebook_id>.+)/nb",
        WorkerGetNb.as_view(),
    ),
    url(
        "api/v1/worker/(?P<session_id>.+)/(?P<worker_id>.+)/(?P<notebook_id>.+)/worker",
        GetWorker.as_view(),
    ),
    url(
        "api/v1/worker/(?P<session_id>.+)/(?P<worker_id>.+)/(?P<notebook_id>.+)/set-worker-state",
        SetWorkerState.as_view(),
    ),
    url(
        "api/v1/worker/(?P<session_id>.+)/(?P<worker_id>.+)/(?P<notebook_id>.+)/delete-worker",
        DeleteWorker.as_view(),
    ),
]
