from django.conf.urls import url

from apps.notebooks.views import ListNotebooks, RetrieveNotebook

notebooks_urlpatterns = [
    url("api/v1/notebooks/(?P<notebook_id>.+)", RetrieveNotebook.as_view()),
    url("api/v1/notebooks", ListNotebooks.as_view()),
]
