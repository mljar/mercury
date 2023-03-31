import logging

from django.db.models import Q
from django.http import JsonResponse
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
    get_site_bucket_key,
    get_worker_bucket_key,
)

log = logging.getLogger(__name__)


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


class WorkerAddFile(APIView):
    def post(self, request, format=None):
        worker_id = request.data.get("worker_id")
        session_id = request.data.get("session_id")
        notebook_id = request.data.get("notebook_id")

        filename = request.data.get("filename", "").replace(" ", "-")
        filepath = request.data.get("filepath")
        output_dir = request.data.get("output_dir")
        local_filepath = request.data.get("local_filepath")

        workers = Worker.objects.filter(
            pk=worker_id, session_id=session_id, notebook__id=notebook_id
        )
        if not workers:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # remove previous objects with the same filepath
        WorkerFile.objects.filter(filepath=filepath, output_dir=output_dir).delete()

        # create a new object
        WorkerFile.objects.create(
            filename=filename,
            filepath=filepath,
            output_dir=output_dir,
            local_filepath=local_filepath,
            created_by=workers[0],
        )

        return Response(status=status.HTTP_200_OK)


class WorkerGetUploadedFilesUrls(APIView):
    def get(
        self,
        request,
        session_id,
        worker_id,
        notebook_id,
        format=None,
    ):
        try:
            # check if such worker exists
            worker = Worker.objects.get(
                pk=worker_id, session_id=session_id, notebook__id=notebook_id
            )
            client_action = "get_object"

            s3 = S3()
            files = UploadedFile.objects.filter(hosted_on=worker.notebook.hosted_on)
            urls = []
            for f in files:
                urls += [s3.get_presigned_url(f.filepath, client_action)]

            return Response({"urls": urls})

        except Exception as e:
            log.exception("Cant get uploaded files urls for worker")

        return Response(status=status.HTTP_403_FORBIDDEN)
