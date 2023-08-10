import os
import json
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
from apps.workers.models import (
    Worker,
    Machine,
    WorkerSession,
)
from apps.workers.constants import WorkerState, MachineState, WorkerSessionState
from apps.workers.serializers import WorkerSerializer
from apps.storage.s3utils import clean_worker_files
from apps.accounts.serializers import UserSerializer

MACHINE_SPELL = os.environ.get("MACHINE_SPELL")


class WorkerGetNb(APIView):
    authentication_classes = []

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


class WorkerGetOwnerAndUser(APIView):
    authentication_classes = []

    def get(self, request, session_id, worker_id, notebook_id, format=None):
        try:
            wrk = Worker.objects.get(
                pk=worker_id, session_id=session_id, notebook__id=notebook_id
            )
            nb = Notebook.objects.get(pk=notebook_id)

            owner = nb.created_by
            user = wrk.run_by
            owner_info = json.loads(owner.profile.info)
            plan = owner_info.get("plan", "starter")

            data = {
                "owner": {
                    "username": owner.username,
                    "email": owner.email,
                    "plan": owner_info.get("plan", "starter"),
                },
                "user": {},
            }
            if user is not None:
                data["user"] = {"username": user.username, "email": user.email}
            return Response(data)
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

            sessions = WorkerSession.objects.filter(worker=worker)
            if sessions:
                session = sessions[len(sessions) - 1]
                session.worker = worker
                session.ipv4 = worker.machine_id
                session.state = WorkerSessionState.Running
                session.save()

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
            sessions = WorkerSession.objects.filter(worker=worker)
            if sessions:
                session = sessions[len(sessions) - 1]
                session.worker = None
                session.state = WorkerSessionState.Stopped
                session.save()

            # delete worker output files
            clean_worker_files(worker.notebook.hosted_on.id, worker.session_id)

            worker.delete()

            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception:
            pass
        return Response(status=status.HTTP_404_NOT_FOUND)


class MachineInfo(APIView):
    def post(self, request, format=None):
        try:
            if MACHINE_SPELL is None:
                return Response(status=status.HTTP_403_FORBIDDEN)
            if MACHINE_SPELL != request.data.get("machine_spell", ""):
                return Response(status=status.HTTP_403_FORBIDDEN)

            ipv4 = request.data.get("ipv4", "")
            if ipv4 == "":
                return Response(status=status.HTTP_400_BAD_REQUEST)

            state = request.data.get("state", "")
            if state not in [s.value for s in MachineState]:
                return Response(status=status.HTTP_400_BAD_REQUEST)

            ms = Machine.objects.filter(ipv4=ipv4)
            if not ms:
                Machine.objects.create(ipv4=ipv4, state=state)
            else:
                for m in ms:
                    m.state = state
                    m.save()

            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception:
            pass
        return Response(status=status.HTTP_404_NOT_FOUND)
