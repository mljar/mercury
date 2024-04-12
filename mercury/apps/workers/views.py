import os
import json
import datetime
import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from django.db.models import Count
from rest_framework import status 
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
from apps.accounts.models import Membership, Site

MACHINE_SPELL = os.environ.get("MACHINE_SPELL")

log = logging.getLogger(__name__)

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


class AnalyticsView(APIView):
    def get(self, request, site_id, format=None):
        try:
            log.info(f"Get analytics for side id {site_id}")
            user = request.user
            if user.is_anonymous:
                return Response(status=status.HTTP_404_NOT_FOUND)

            site = Site.objects.get(pk=site_id)
            # check if have EDIT rights
            if site.created_by != user:
                m = Membership.objects.filter(
                    user=user, host=site, rights=Membership.EDIT
                )
                if not m:
                    return Response(status=status.HTTP_404_NOT_FOUND)

            usage_data = {}
            sessions = (
                WorkerSession.objects.extra(select={"day": "date( updated_at )"})
                .select_related("notebook", "run_by")
                .values("notebook__path", "day")
                .annotate(nbcount=Count("notebook"))
                .filter(site=site, created_at__gte=timezone.now() - timedelta(days=30))
            )
            # generate empty data for all notebooks
            days_list = []
            start = datetime.datetime.now()
            days_index = {}
            for index, day in enumerate(reversed(range(31))):
                day = (start - timedelta(days=day)).strftime("%Y-%m-%d")
                days_list += [day]
                days_index[day] = index
            # fill data
            notebooks = Notebook.objects.filter(hosted_on=site)
            nb_names = [nb.path.split("/")[-1] for nb in notebooks]
            for nb in nb_names:
                usage_data[nb] = {"x": days_list, "y": [0] * len(days_list)}
            
            for session in sessions:
                nb = session["notebook__path"].split("/")[-1]
                if nb in usage_data:
                    if isinstance(session["day"], str):
                        day = session["day"]
                    else:
                        day = session["day"].strftime("%Y-%m-%d")
                    if day in days_index:
                        usage_data[nb]["y"][days_index[day]] = session["nbcount"]   
            
            users_data = []
            logged_users_sessions = (
                WorkerSession.objects.extra(select={"day": "date( updated_at )"})
                .select_related("notebook", "run_by")
                .values("notebook__path", "day", "run_by__username")
                .filter(site=site, created_at__gte=timezone.now() - timedelta(days=30))
                .exclude(run_by__isnull=True)
                .distinct()
            )
            for session in logged_users_sessions:
                users_data += [
                    {
                        "day": session["day"],
                        "username": session["run_by__username"],
                        "notebook": session["notebook__path"].split("/")[-1],
                    }
                ]

            return Response(
                {"usage_data": usage_data, "users_data": users_data},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            log.error(f"User analytics error, {str(e)}")
        return Response(status=status.HTTP_404_NOT_FOUND)
