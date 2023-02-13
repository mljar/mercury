import json
import os
import shutil
import uuid

from celery.result import AsyncResult
from django.conf import settings
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from requests import request
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notebooks.models import Notebook
from apps.notebooks.views import notebooks_queryset
from apps.storage.storage import StorageManager
from apps.tasks.models import Task
from apps.tasks.serializers import TaskSerializer
from apps.tasks.tasks import task_execute
from apps.tasks.tasks_export import export_to_pdf


class TaskCreateView(CreateAPIView):
    serializer_class = TaskSerializer
    queryset = Task.objects.all()

    def perform_create(self, serializer):
        notebook = get_object_or_404(
            notebooks_queryset(self.request), pk=self.kwargs["notebook_id"]
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
        notebook = get_object_or_404(
            notebooks_queryset(self.request), pk=self.kwargs["notebook_id"]
        )
        try:
            if notebook.schedule is None or notebook.schedule == "":
                return Task.objects.filter(
                    notebook_id=self.kwargs["notebook_id"],
                    session_id=self.kwargs["session_id"],
                ).latest("id")
            else:
                return Task.objects.filter(
                    notebook_id=self.kwargs["notebook_id"]
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


class ListWorkerOutputFilesView(APIView):
    def get(self, request, session_id, worker_id, format=None):
        files_urls = []
        if settings.STORAGE == settings.STORAGE_MEDIA:
            sm = StorageManager(session_id, worker_id)
            files_urls = sm.list_worker_files_urls()

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

        return Response(status=status.HTTP_204_NO_CONTENT)


class CreateRestAPITask(APIView):
    def post(self, request, notebook_slug):
        try:
            notebook = (
                notebooks_queryset(request).filter(slug=notebook_slug).latest("id")
            )
        except Notebook.DoesNotExist:
            raise Http404()
        try:
            with transaction.atomic():
                task = Task(
                    session_id=uuid.uuid4().hex,
                    state="CREATED",
                    notebook=notebook,
                    params=json.dumps(request.data),
                )
                task.save()
                job_params = {"db_id": task.id}
                transaction.on_commit(lambda: task_execute.delay(job_params))
            return Response({"id": task.session_id}, status=status.HTTP_201_CREATED)
        except Exception as e:
            raise APIException(str(e))


class GetRestAPITask(APIView):
    def get(self, requset, session_id):
        try:
            task = Task.objects.filter(
                session_id=session_id,
            ).latest("id")

            if task.state == "DONE":
                response = {}
                try:
                    fname = os.path.join(
                        settings.MEDIA_ROOT, task.session_id, "response.json"
                    )
                    if os.path.exists(fname):
                        with open(fname) as fin:
                            response = json.loads(fin.read())
                except Exception as e:
                    return Response(
                        str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                return Response(response, status=status.HTTP_200_OK)
            if task.state == "ERROR":
                return Response(
                    task.result, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            return Response({"state": "running"}, status=status.HTTP_202_ACCEPTED)
        except Task.DoesNotExist:
            raise Http404()


class ExportPDF(APIView):
    def post(self, request):
        try:
            # check if user can access the notebook
            notebook = notebooks_queryset(request).get(pk=request.data["notebook_id"])
        except Notebook.DoesNotExist:
            raise Http404()
        try:
            celery_job = export_to_pdf.delay(request.data)
            return Response({"job_id": celery_job.id}, status=status.HTTP_201_CREATED)
        except Exception as e:
            raise APIException(str(e))


class GetPDFAddress(APIView):
    def get(self, request, job_id):
        res = AsyncResult(job_id)
        fileUrl, title, error = "", "", ""
        if res.ready():
            if res.state == "FAILURE":
                error = str(res.result)
            elif res.state == "SUCCESS":
                fileUrl, title = res.result
        return Response(
            {"ready": res.ready(), "url": fileUrl, "title": title, "error": error}
        )


class ExecutionHistoryView(ListAPIView):
    serializer_class = TaskSerializer
    queryset = Task.objects.all()

    def get_queryset(self):
        # check if user has access to the notebook
        notebook = get_object_or_404(
            notebooks_queryset(self.request), pk=self.kwargs["notebook_id"]
        )

        return Task.objects.filter(
            notebook_id=notebook.id,
            session_id=self.kwargs["session_id"],
        )
