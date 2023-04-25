from django.urls import re_path

from apps.notebooks.views import (
    GetNbIframes,
    ListNotebooks,
    RetrieveNotebook,
    RetrieveNotebookWithSlug,
)

notebooks_urlpatterns = [
    re_path(
        "api/v1/(?P<site_id>.+)/notebooks/(?P<notebook_id>.+)",
        RetrieveNotebook.as_view(),
    ),
    re_path(
        "api/v1/(?P<site_id>.+)/getnb/(?P<notebook_slug>.+)",
        RetrieveNotebookWithSlug.as_view(),
    ),
    re_path("api/v1/(?P<site_id>.+)/notebooks", ListNotebooks.as_view()),
    re_path("api/v1/(?P<site_id>.+)/nb-iframes", GetNbIframes.as_view()),
]
