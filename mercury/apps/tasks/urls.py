from django.conf.urls import include, url
from rest_framework.routers import DefaultRouter

from apps.tasks.views import (
    ClearTasksView,
    CreateRestAPITask,
    ExecutionHistoryView,
    ExportPDF,
    GetLastTaskView,
    GetPDFAddress,
    GetRestAPITask,
    ListOutputFilesView,
    ListWorkerOutputFilesView,
    TaskCreateView,
)

tasks_urlpatterns = [
    url("api/v1/execute/(?P<notebook_id>.+)", TaskCreateView.as_view()),
    url(
        "api/v1/latest_task/(?P<notebook_id>.+)/(?P<session_id>.+)",
        GetLastTaskView.as_view(),
    ),
    url(
        "api/v1/output_files/(?P<session_id>.+)/(?P<task_id>.+)",
        ListOutputFilesView.as_view(),
    ),
    url(
        "api/v1/worker_output_files/(?P<session_id>.+)/(?P<worker_id>.+)",
        ListWorkerOutputFilesView.as_view(),
    ),
    url(
        "api/v1/clear_tasks/(?P<notebook_id>.+)/(?P<session_id>.+)",
        ClearTasksView.as_view(),
    ),
    # used by notebook as REST API
    url("run/(?P<notebook_slug>.+)", CreateRestAPITask.as_view()),
    url("get/(?P<session_id>.+)", GetRestAPITask.as_view()),
    url("export_pdf", ExportPDF.as_view()),
    url("get_pdf/(?P<job_id>.+)", GetPDFAddress.as_view()),
    url(
        "api/v1/execution_history/(?P<notebook_id>.+)/(?P<session_id>.+)",
        ExecutionHistoryView.as_view(),
    ),
]
