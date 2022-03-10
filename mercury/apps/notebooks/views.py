from django.db import transaction
from django.db.models import Q
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


class NotebookListView(viewsets.ReadOnlyModelViewSet):

    serializer_class = NotebookSerializer

    def in_commas(self, word):
        return "," + word + ","

    def get_queryset(self):
        if not is_pro:
            return Notebook.objects.all()

        user = self.request.user
        if user.is_anonymous:
            return Notebook.objects.filter(share=self.in_commas("public"))

        q_list = (
            Q(share=self.in_commas("public"))
            | Q(share=self.in_commas("private"))
            | Q(share__icontains=self.in_commas(user.username))
        )

        for m in Membership.objects.filter(user=user):
            q_list |= Q(share__icontains=self.in_commas(m.group.name))

        return Notebook.objects.filter(q_list)

    def retrieve(self, request, pk=None):
        notebook = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = NotebookSerializer(notebook)
        if notebook.state.startswith("WATCH"):
            task_watch.delay(notebook.id)

        return Response(serializer.data)
