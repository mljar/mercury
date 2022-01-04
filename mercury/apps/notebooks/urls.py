from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from apps.notebooks.views import NotebookListView

router = DefaultRouter()
router.register("notebooks", NotebookListView, basename="notebooks")
notebooks_urlpatterns = [url("api/v1/", include(router.urls))]
