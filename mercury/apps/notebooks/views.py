from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.notebooks.models import Notebook
from apps.notebooks.serializers import NotebookSerializer
from apps.notebooks.tasks import task_init_notebook, task_watch


class NotebookListView(viewsets.ReadOnlyModelViewSet):

    serializer_class = NotebookSerializer
    queryset = Notebook.objects.all()

    def retrieve(self, request, pk=None):
        notebook = get_object_or_404(self.queryset, pk=pk)
        serializer = NotebookSerializer(notebook)
        if notebook.state.startswith("WATCH"):
            task_watch.delay(notebook.id)

        return Response(serializer.data)
