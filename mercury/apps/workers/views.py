from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notebooks.models import Notebook
from apps.notebooks.serializers import NotebookSerializer
from apps.workers.models import Worker, WorkerState
from apps.workers.serializers import WorkerSerializer


class WorkerGetNb(APIView):
    def get(self, request, session_id, worker_id, notebook_id, format=None):
        try:
            Worker.objects.get(
                pk=worker_id, session_id=session_id, notebook__id=notebook_id
            )
            nb = Notebook.objects.get(pk=notebook_id)
            return Response(NotebookSerializer(nb).data)
        except Exception:
            pass
        return Response(status=status.HTTP_404_NOT_FOUND)


class WorkerUpdateNb(APIView):
    def post(self, request, session_id, worker_id, notebook_id, format=None):
        try:
            Worker.objects.get(
                pk=worker_id, session_id=session_id, notebook__id=notebook_id
            )
            nb = Notebook.objects.get(pk=notebook_id)
            nb.title = request.data.get("title", nb.title)
            nb.params = request.data.get("params", nb.params)
            nb.save()
            return Response(NotebookSerializer(nb).data)
        except Exception:
            pass
        return Response(status=status.HTTP_404_NOT_FOUND)


class GetWorker(APIView):
    def get(self, request, session_id, worker_id, notebook_id, format=None):
        try:
            worker = Worker.objects.get(
                pk=worker_id, session_id=session_id, notebook__id=notebook_id
            )
            return Response(WorkerSerializer(worker).data)
        except Exception:
            pass
        return Response(status=status.HTTP_404_NOT_FOUND)


class IsWorkerStale(APIView):
    def get(self, request, session_id, worker_id, notebook_id, format=None):
        try:
            worker = Worker.objects.get(
                pk=worker_id, session_id=session_id, notebook__id=notebook_id
            )

            is_stale = worker.updated_at < timezone.now() - timedelta(
                minutes=settings.WORKER_STALE_TIME
            )
            return Response({"is_stale": is_stale})
        except Exception:
            pass
        return Response(status=status.HTTP_404_NOT_FOUND)


class SetWorkerState(APIView):
    def post(self, request, session_id, worker_id, notebook_id, format=None):
        try:
            worker = Worker.objects.get(
                pk=worker_id, session_id=session_id, notebook__id=notebook_id
            )
            worker.state = request.data.get("state", WorkerState.Unknown)
            if request.data.get("machine_id") is not None:
                worker.machine_id = request.data.get("machine_id")
            worker.save()
            return Response(WorkerSerializer(worker).data)
        except Exception:
            pass
        return Response(status=status.HTTP_404_NOT_FOUND)


class DeleteWorker(APIView):
    def post(self, request, session_id, worker_id, notebook_id, format=None):
        try:
            worker = Worker.objects.get(
                pk=worker_id, session_id=session_id, notebook__id=notebook_id
            )
            worker.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception:
            pass
        return Response(status=status.HTTP_404_NOT_FOUND)
