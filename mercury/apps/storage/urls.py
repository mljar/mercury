from django.urls import re_path

from apps.storage.views import (
    FileUploaded,
    ListFiles,
    PresignedUrl,
    FileUploaded,
    FileNotUploaded,
)

storage_urlpatterns = [
    re_path("api/v1/(?P<site_id>.+)/files", ListFiles.as_view()),
    re_path(
        "api/v1/presigned-re_path/(?P<action>.+)/(?P<site_id>.+)/(?P<filename>.+)",
        PresignedUrl.as_view(),
    ),
    re_path(
        "api/v1/file-uploaded",
        FileUploaded.as_view(),
    ),
    re_path(
        "api/v1/file-not-uploaded",
        FileNotUploaded.as_view(),
    ),
]
