import os
import shutil

from django.conf import settings
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notebooks.models import Notebook
from apps.notebooks.views import NotebookListView
from apps.tasks.models import Task
from apps.tasks.serializers import TaskSerializer
from apps.tasks.tasks import task_execute


class TaskCreateView(CreateAPIView):

    serializer_class = TaskSerializer
    queryset = Task.objects.all()

    def perform_create(self, serializer):
        list_view = NotebookListView(request=self.request)
        notebook = get_object_or_404(
            list_view.get_queryset(), pk=self.kwargs["notebook_id"]
        )
        try:
            with transaction.atomic():
                instance = serializer.save(
                    state="CREATED",
                    notebook=notebook,
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


class ListOutputFilesView(APIView):
    def get(self, request, session_id, task_id, format=None):
        files_urls = []
        try:
            output_dir = os.path.join(
                settings.MEDIA_ROOT, session_id, f"output_{task_id}"
            )
            for f in os.listdir(output_dir):
                if os.path.isfile(os.path.join(output_dir, f)):
                    files_urls += [
                        f"{settings.MEDIA_URL}/{session_id}/output_{task_id}/{f}"
                    ]
        except Exception as e:
            print(
                f"Trying to list files for session_id {session_id} and task_id {task_id}"
            )
            print("Exception occured", str(e))
        return Response(files_urls)


class ClearTasksView(APIView):
    def post(self, request, notebook_id, session_id, format=None):

        try:
            tasks = Task.objects.filter(notebook_id=notebook_id, session_id=session_id)

            for task in tasks:
                output_file = os.path.join(
                    settings.MEDIA_ROOT, session_id, f"output_{task.id}.html"
                )
                output_dir = os.path.join(
                    settings.MEDIA_ROOT, session_id, f"output_{task.id}"
                )

                try:
                    if os.path.isfile(output_file):
                        os.remove(output_file)
                    if os.path.isdir(output_dir):
                        shutil.rmtree(output_dir)
                except Exception as e:
                    print(f"Trying to delete {output_file} and {output_dir}")
                    print(str(e))

            tasks.delete()

        except Exception as e:
            print(
                f"Trying to clear tasks for notebook_id {notebook_id} and session_id {session_id}"
            )
            print("Exception occured", str(e))

        return Response(status.HTTP_204_NO_CONTENT)
