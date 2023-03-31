import logging

from django.db.models import Q
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Membership, Site
from apps.notebooks.models import Notebook
from apps.storage.models import UserUploadedFile
from apps.storage.s3utils import S3
from apps.storage.serializers import UploadedFileSerializer
from apps.workers.models import Worker
from apps.accounts.views.utils import is_cloud_version

from apps.accounts.views.sites import (
    get_plan,
    PLAN_KEY,
    PLAN_STARTER,
    PLAN_PRO,
    PLAN_BUSINESS,
)

from apps.storage.utils import get_bucket_key, get_user_upload_bucket_key
from apps.storage.views.dashboardfiles import FILE_LIMITS

log = logging.getLogger(__name__)


def user_upload_allowed(user, site_id):
    try:
        sites = Site.objects.filter(pk=site_id)

        if not sites:
            return False
        if sites[0].share == Site.PUBLIC:
            return True
        if sites[0].share == Site.PRIVATE and user.is_anonymous:
            return False

        sites = sites.filter(
            Q(pk__in=Membership.objects.filter(user=user).values("host__id"))
            | Q(created_by=user)
        )
        if not sites:
            return False
        return True
    except Exception as e:
        pass
    return False


def upload_allowed_check_limits(user, site_id, filesize):
    try:
        if not is_cloud_version():
            return True

        site = Site.objects.get(pk=site_id)
        plan = get_plan(site.created_by)
        files_size_limit = FILE_LIMITS[plan]["size"]  # in MB

        if int(filesize) / 1024 / 1024 > files_size_limit:
            return False
        return True
    except Exception as e:
        pass
    return False


class NbPresignedUrlPut(APIView):
    def get(self, request, site_id, session_id, filename, filesize, format=None):
        site_id = int(site_id)

        if not user_upload_allowed(request.user, site_id):
            return Response(status=status.HTTP_403_FORBIDDEN)

        if not upload_allowed_check_limits(request.user, site_id, filesize):
            return Response(status=status.HTTP_403_FORBIDDEN)

        client_action = "put_object"
        s3 = S3()
        url = s3.get_presigned_url(
            get_user_upload_bucket_key(site_id, session_id, filename.replace(" ", "-")),
            client_action,
        )
        return Response({"url": url})


class NbFileUploaded(APIView):
    def post(self, request, format=None):
        site_id = int(request.data.get("site_id"))
        session_id = request.data.get("session_id")
        filename = request.data.get("filename", "").replace(" ", "-")

        bucket_key = get_user_upload_bucket_key(site_id, session_id, filename)

        s3 = S3()
        if not s3.file_exists(bucket_key):
            return Response(status=status.HTTP_403_FORBIDDEN)

        site = Site.objects.get(pk=site_id)
        # remove previous objects with the same filepath
        UserUploadedFile.objects.filter(
            filepath=bucket_key, session_id=session_id, hosted_on=site
        ).delete()

        # create a new object
        upload = UserUploadedFile.objects.create(
            filename=filename,
            filepath=bucket_key,
            session_id=session_id,
            hosted_on=site,
        )

        return Response(status=status.HTTP_200_OK)


class NbDeleteFile(APIView):
    def post(self, request, format=None):
        site_id = int(request.data.get("site_id"))
        session_id = request.data.get("session_id")
        filename = request.data.get("filename", "").replace(" ", "-")
        bucket_key = get_user_upload_bucket_key(site_id, session_id, filename)

        s3 = S3()
        s3.delete_file(bucket_key)

        UserUploadedFile.objects.filter(
            filepath=bucket_key, session_id=session_id, hosted_on__id=site_id
        ).delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class WorkerGetNbFileUrl(APIView):
    def get(
        self,
        request,
        session_id,
        worker_id,
        notebook_id,
        filename,
        format=None,
    ):
        try:
            # check if such worker exists
            worker = Worker.objects.get(
                pk=int(worker_id), session_id=session_id, notebook__id=int(notebook_id)
            )

            upload = UserUploadedFile.objects.filter(
                filename=filename.replace(" ", "-"), session_id=session_id
            ).latest("id")

            client_action = "get_object"
            s3 = S3()

            return Response(
                {"url": s3.get_presigned_url(upload.filepath, client_action)}
            )

        except Exception as e:
            log.exception("Cant get user uploaded file url for worker")

        return Response(status=status.HTTP_403_FORBIDDEN)
