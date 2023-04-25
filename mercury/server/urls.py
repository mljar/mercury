from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import render
from django.urls import path, re_path

from apps.notebooks.urls import notebooks_urlpatterns
from apps.tasks.urls import tasks_urlpatterns
from apps.accounts.urls import accounts_urlpatterns
from apps.storage.urls import storage_urlpatterns
from apps.workers.urls import workers_urlpatterns
from server.views import VersionInfo, WelcomeMessage

urlpatterns = []

if settings.DEBUG or settings.SERVE_STATIC:
    # serve static file for development only!
    def index(request):
        return render(request, "index.html")

    # Serve static and media files from development server
    urlpatterns += [
        path("", index),
        re_path(r"^app", index),
        re_path(r"^login", index),
        re_path(r"^account", index),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


urlpatterns += [
    path("admin/", admin.site.urls),
    re_path(
        "api/v1/version",
        VersionInfo.as_view(),
    ),
    re_path(
        "api/v1/(?P<site_id>.+)/welcome",
        WelcomeMessage.as_view(),
    ),
    re_path(r"^api/v1/fp/", include("django_drf_filepond.urls")),
]

urlpatterns += tasks_urlpatterns
urlpatterns += notebooks_urlpatterns
urlpatterns += accounts_urlpatterns
urlpatterns += storage_urlpatterns
urlpatterns += workers_urlpatterns

admin.site.site_header = "Mercury Admin Panel"
