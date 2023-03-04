from django.conf.urls import url

from apps.storage.views import FileUploaded, ListFiles, GetPutPresignedUrl, FileUploaded

notebooks_urlpatterns = [
    url("api/v1/(?P<site_id>.+)/files", ListFiles.as_view()),
    url(
        "api/v1/put-presigned-url/(?P<site_id>.+)/(?P<filename>.+)",
        GetPutPresignedUrl.as_view(),
    ),
    url(
        "api/v1/file-uploaded",
        FileUploaded.as_view(),
    ),
]
