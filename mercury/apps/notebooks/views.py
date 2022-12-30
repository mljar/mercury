from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notebooks.models import Notebook
from apps.notebooks.serializers import NotebookSerializer
from apps.notebooks.tasks import task_init_notebook, task_watch
from server.settings import is_pro

if is_pro:
    from pro.accounts.models import Membership


def in_commas(word):
    return "," + word + ","


def notebooks_queryset(request):
    if not is_pro:
        return Notebook.objects.all()

    user = request.user
    if user.is_anonymous:
        return Notebook.objects.filter(share=in_commas("public"))

    q_list = (
        Q(share=in_commas("public"))
        | Q(share=in_commas("private"))
        | Q(share__icontains=in_commas(user.username))
    )

    for m in Membership.objects.filter(user=user):
        q_list |= Q(share__icontains=in_commas(m.group.name))

    return Notebook.objects.filter(q_list)


class ListNotebooks(APIView):
    def get(self, request, format=None):
        notebooks = notebooks_queryset(request)
        serializer = NotebookSerializer(notebooks, many=True)
        return JsonResponse(serializer.data, safe=False)


class RetrieveNotebook(APIView):
    def get(self, request, notebook_id, format=None):
        pk = int(notebook_id.replace("/", ""))
        notebook = get_object_or_404(notebooks_queryset(request), pk=pk)
        serializer = NotebookSerializer(notebook)
        if notebook.state.startswith("WATCH"):
            task_watch.delay(notebook.id)

        return JsonResponse(serializer.data, safe=False)
