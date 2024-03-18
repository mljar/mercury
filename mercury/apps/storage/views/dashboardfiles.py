import logging

from django.db.models import Q
from django.http import JsonResponse
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Membership, Site
from apps.notebooks.models import Notebook
from apps.storage.models import UploadedFile, WorkerFile
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

from apps.storage.utils import (
    get_bucket_key,
    get_worker_bucket_key,
)

log = logging.getLogger(__name__)


class GetStorageType(APIView):
    def get(self, request, format=None):
        return Response({"storage_type": settings.STORAGE})


def get_site(user, site_id):
    if user.is_anonymous:
        return None

    sites = Site.objects.filter(
        Q(pk=site_id)
        & (
            Q(
                pk__in=Membership.objects.filter(
                    user=user, rights=Membership.EDIT
                ).values("host__id")
            )
            | Q(created_by=user)
        )
    )

    if not sites:
        return None
    return sites[0]


class ListFiles(APIView):
    def get(self, request, site_id, format=None):
        site = get_site(request.user, site_id)
        if site is None:
            return Response(status=status.HTTP_403_FORBIDDEN)

        files = UploadedFile.objects.filter(hosted_on=site)

        return Response(UploadedFileSerializer(files, many=True).data)


class PresignedUrl(APIView):
    def get(self, request, action, site_id, filename, format=None):
        site = get_site(request.user, site_id)
        if site is None:
            return Response(status=status.HTTP_403_FORBIDDEN)

        client_action = (
            "put_object" if action in ["put", "put_object"] else "get_object"
        )

        s3 = S3()
        url = s3.get_presigned_url(
            get_bucket_key(site, request.user, filename.replace(" ", "-")),
            client_action,
        )
        return Response({"url": url})


FILE_LIMITS = {
    PLAN_STARTER: {
        "files": 2,
        "size": 5,
    },
    PLAN_PRO: {"files": 25, "size": 50},
    PLAN_BUSINESS: {"files": 50, "size": 100},  # MB
}


def upload_allowed_check_limits(user, site_id, filesize):
    if not is_cloud_version():
        return True
    plan = get_plan(user)
    files_count_limit = FILE_LIMITS[plan]["files"]
    files_size_limit = FILE_LIMITS[plan]["size"]  # in MB

    if int(filesize) / 1024 / 1024 > files_size_limit:
        return False

    total_files = UploadedFile.objects.filter(hosted_on__id=site_id)
    if total_files.count() >= files_count_limit:
        return False

    return True


class GetUploadCountLimit(APIView):
    def get(self, request, site_id, format=None):
        site = get_site(request.user, site_id)
        if site is None:
            return Response(status=status.HTTP_403_FORBIDDEN)

        if not is_cloud_version():
            # no limit for local version
            return Response({"count": 1000})
        
        plan = get_plan(request.user)
        count_limit = FILE_LIMITS[plan]["files"]
        total_files = UploadedFile.objects.filter(hosted_on__id=site_id)
        
        return Response({"count": count_limit - total_files.count()})


class PresignedUrlPut(APIView):
    def get(self, request, site_id, filename, filesize, format=None):
        site = get_site(request.user, site_id)
        if site is None:
            return Response(status=status.HTTP_403_FORBIDDEN)

        upload_allowed = upload_allowed_check_limits(request.user, site_id, filesize)
        if not upload_allowed:
            return Response(status=status.HTTP_403_FORBIDDEN)

        client_action = "put_object"
        s3 = S3()
        url = s3.get_presigned_url(
            get_bucket_key(site, request.user, filename.replace(" ", "-")),
            client_action,
        )
        return Response({"url": url})


class WorkerPresignedUrl(APIView):
    def get(
        self,
        request,
        action,
        session_id,
        worker_id,
        notebook_id,
        output_dir,
        filename,
        format=None,
    ):
        try:
            # check if such worker exists
            Worker.objects.get(
                pk=worker_id, session_id=session_id, notebook__id=notebook_id
            )
            client_action = (
                "put_object" if action in ["put", "put_object"] else "get_object"
            )

            s3 = S3()
            url = s3.get_presigned_url(
                get_worker_bucket_key(
                    session_id, output_dir, filename.replace(" ", "-")
                ),
                client_action,
            )

            return Response({"url": url})

        except Exception as e:
            log.exception("Cant create presigned url for worker")

        return Response(status=status.HTTP_403_FORBIDDEN)


class FileUploaded(APIView):
    def post(self, request, format=None):
        site_id = request.data.get("site_id")
        filename = request.data.get("filename", "").replace(" ", "-")
        filesize = request.data.get("filesize")
        filetype = filename.split(".")[-1].lower()

        site = get_site(request.user, site_id)
        if site is None:
            return Response(status=status.HTTP_403_FORBIDDEN)

        bucket_key = get_bucket_key(site, request.user, filename)

        # remove previous objects with the same filepath
        UploadedFile.objects.filter(filepath=bucket_key, hosted_on=site).delete()

        # create a new object
        UploadedFile.objects.create(
            filename=filename,
            filepath=bucket_key,
            filetype=filetype,
            filesize=filesize,
            hosted_on=site,
            created_by=request.user,
        )

        return Response(status=status.HTTP_200_OK)


class DeleteFile(APIView):
    def post(self, request, format=None):
        site_id = request.data.get("site_id")
        filename = request.data.get("filename", "").replace(" ", "-")

        site = get_site(request.user, site_id)
        if site is None:
            return Response(status=status.HTTP_403_FORBIDDEN)

        bucket_key = get_bucket_key(site, request.user, filename)

        s3 = S3()
        s3.delete_file(bucket_key)

        UploadedFile.objects.filter(filepath=bucket_key, hosted_on=site).delete()

        Notebook.objects.filter(path__icontains=filename, hosted_on=site).delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
