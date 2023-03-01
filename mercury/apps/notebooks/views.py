from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Membership
from apps.notebooks.models import Notebook
from apps.notebooks.serializers import NotebookSerializer
from apps.notebooks.tasks import task_init_notebook, task_watch
from apps.accounts.models import Site, Membership

def in_commas(word):
    return "," + word + ","


def notebooks_queryset(request, site_id):
    user = request.user
    if user.is_anonymous:
        return Notebook.objects.filter(hosted_on__id=site_id, hosted_on__share=Site.PUBLIC)

    # it can be optimized
    site = Site.objects.get(pk=site_id)
    if site.share == Site.PUBLIC:
        return Notebook.objects.filter(hosted_on=site)

    # admin can see all notebooks on site
    if site.created_by == user:
        return Notebook.objects.filter(hosted_on=site)    

    # don't filter on rights because both VIEW and EDIT allows
    # to see and execute notebooks
    m = Membership.objects.filter(user=user, host=site)
    if m:
        return Notebook.objects.filter(hosted_on=site)
    return Notebook.objects.filter(hosted_on=site, created_by=user)

class ListNotebooks(APIView):
    def get(self, request, site_id, format=None):
        notebooks = notebooks_queryset(request, site_id).order_by("slug")
        serializer = NotebookSerializer(notebooks, many=True)
        return JsonResponse(serializer.data, safe=False)


class RetrieveNotebook(APIView):
    def get(self, request, site_id, notebook_id, format=None):
        pk = int(notebook_id.replace("/", ""))
        notebook = get_object_or_404(notebooks_queryset(request, site_id), pk=pk)
        serializer = NotebookSerializer(notebook)
        if notebook.state.startswith("WATCH"):
            task_watch.delay(notebook.id)

        return JsonResponse(serializer.data, safe=False)


class RetrieveNotebookWithSlug(APIView):
    def get(self, request, site_id, notebook_slug, format=None):
        notebook_slug = notebook_slug.replace("/", "")

        notebooks = notebooks_queryset(request, site_id).filter(slug=notebook_slug)

        if not notebooks:
            return JsonResponse({}, status=status.HTTP_404_NOT_FOUND)

        # get the first one - it should be only one :)
        serializer = NotebookSerializer(notebooks[0])
        return JsonResponse(serializer.data, safe=False)
