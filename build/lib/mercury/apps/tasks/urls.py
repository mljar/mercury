from django.conf.urls import include, url
from rest_framework.routers import DefaultRouter

from apps.tasks.views import (ClearTasksView, GetLastTaskView,
                              ListOutputFilesView, TaskCreateView)

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
        "api/v1/clear_tasks/(?P<notebook_id>.+)/(?P<session_id>.+)",
        ClearTasksView.as_view(),
    ),
]
