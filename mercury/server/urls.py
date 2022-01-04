from django.conf import settings
from django.contrib import admin
from django.urls import path, re_path
from django.conf.urls import url
from django.shortcuts import render
from django.conf.urls.static import static

from apps.tasks.urls import tasks_urlpatterns
from apps.notebooks.urls import notebooks_urlpatterns

from server.views import VersionInfo

urlpatterns = [
    path("admin/", admin.site.urls),
    url(
        "api/v1/version",
        VersionInfo.as_view(),
    ),
]

urlpatterns += tasks_urlpatterns
urlpatterns += notebooks_urlpatterns

if settings.DEBUG or settings.SERVE_STATIC:
    # serve static file for development only!
    def index(request):
        return render(request, "index.html")

    # Serve static and media files from development server
    urlpatterns += [
        path("", index),
        re_path("app", index),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


admin.site.site_header = "Mercury Admin Panel"
