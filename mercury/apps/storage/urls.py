from django.urls import re_path

from apps.storage.views import (
    DeleteFile,
    FileUploaded,
    ListFiles,
    PresignedUrl,
    WorkerPresignedUrl,
    WorkerAddFile,
    WorkerGetUploadedFilesUrls,
)

storage_urlpatterns = [
    re_path("api/v1/(?P<site_id>.+)/files", ListFiles.as_view()),
    re_path(
        "api/v1/presigned-url/(?P<action>.+)/(?P<site_id>.+)/(?P<filename>.+)",
        PresignedUrl.as_view(),
    ),
    re_path(
        "api/v1/file-uploaded",
        FileUploaded.as_view(),
    ),
    re_path(
        "api/v1/delete-file",
        DeleteFile.as_view(),
    ),
    re_path(
        "api/v1/worker/presigned-url/(?P<action>.+)/(?P<session_id>.+)/(?P<worker_id>.+)/(?P<notebook_id>.+)/(?P<output_dir>.+)/(?P<filename>.+)",
        WorkerPresignedUrl.as_view(),
    ),
    re_path(
        "api/v1/worker/add-file",
        WorkerAddFile.as_view(),
    ),
    re_path(
        "api/v1/worker/uploaded-files-urls/(?P<session_id>.+)/(?P<worker_id>.+)/(?P<notebook_id>.+)",
        WorkerGetUploadedFilesUrls.as_view(),
    ),
]
