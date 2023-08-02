from django.urls import re_path

from apps.workers.views import (
    DeleteWorker,
    GetWorker,
    IsWorkerStale,
    SetWorkerState,
    WorkerGetNb,
    WorkerUpdateNb,
    MachineInfo,
    WorkerGetOwnerAndUser,
)

workers_urlpatterns = [
    re_path(
        "api/v1/worker/(?P<session_id>.+)/(?P<worker_id>.+)/(?P<notebook_id>.+)/nb",
        WorkerGetNb.as_view(),
    ),
    re_path(
        "api/v1/worker/(?P<session_id>.+)/(?P<worker_id>.+)/(?P<notebook_id>.+)/owner-and-user",
        WorkerGetOwnerAndUser.as_view(),
    ),
    re_path(
        "api/v1/worker/(?P<session_id>.+)/(?P<worker_id>.+)/(?P<notebook_id>.+)/update-nb",
        WorkerUpdateNb.as_view(),
    ),
    re_path(
        "api/v1/worker/(?P<session_id>.+)/(?P<worker_id>.+)/(?P<notebook_id>.+)/worker",
        GetWorker.as_view(),
    ),
    re_path(
        "api/v1/worker/(?P<session_id>.+)/(?P<worker_id>.+)/(?P<notebook_id>.+)/is-worker-stale",
        IsWorkerStale.as_view(),
    ),
    re_path(
        "api/v1/worker/(?P<session_id>.+)/(?P<worker_id>.+)/(?P<notebook_id>.+)/set-worker-state",
        SetWorkerState.as_view(),
    ),
    re_path(
        "api/v1/worker/(?P<session_id>.+)/(?P<worker_id>.+)/(?P<notebook_id>.+)/delete-worker",
        DeleteWorker.as_view(),
    ),
    re_path(
        "api/v1/machine-info",
        MachineInfo.as_view(),
    ),
]
