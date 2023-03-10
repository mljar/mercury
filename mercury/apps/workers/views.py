from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.workers.serializers import WorkerSerializer
from apps.notebooks.models import Notebook
from apps.notebooks.serializers import NotebookSerializer
from apps.workers.models import Worker, WorkerState


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
