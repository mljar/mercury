from django.conf.urls import url

from apps.storage.views import ListFiles

notebooks_urlpatterns = [
    url("api/v1/(?P<site_id>.+)/files", ListFiles.as_view()),
]
