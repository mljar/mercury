from django.db import transaction
from django.http import Http404

from rest_framework.generics import CreateAPIView
from rest_framework.generics import RetrieveAPIView
from rest_framework.exceptions import APIException

from apps.notebooks.models import Notebook
from apps.tasks.models import Task
from apps.tasks.serializers import TaskSerializer

from apps.tasks.tasks import task_execute


class TaskCreateView(CreateAPIView):

    serializer_class = TaskSerializer
    queryset = Task.objects.all()

    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                instance = serializer.save(
                    state="CREATED",
                    notebook=Notebook.objects.get(pk=self.kwargs["notebook_id"]),
                )
                job_params = {"db_id": instance.id}
                transaction.on_commit(lambda: task_execute.delay(job_params))
        except Exception as e:
            raise APIException(str(e))


class GetLastTaskView(RetrieveAPIView):

    serializer_class = TaskSerializer
    queryset = Task.objects.all()

    def get_object(self):
        try:
            return Task.objects.filter(
                notebook_id=self.kwargs["notebook_id"],
                session_id=self.kwargs["session_id"],
            ).latest("id")
        except Task.DoesNotExist:
            raise Http404()
