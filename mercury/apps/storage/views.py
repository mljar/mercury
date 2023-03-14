import logging

from django.db.models import Q
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Membership, Site
from apps.storage.models import UploadedFile, WorkerFile
from apps.storage.s3utils import S3
from apps.storage.serializers import UploadedFileSerializer
from apps.workers.models import Worker


log = logging.getLogger(__name__)


def get_bucket_key(site, user, filename):
    return f"site-{site.id}/user-{user.id}/{filename}"


def get_site_bucket_key(site, filename):
    return f"site-{site.id}/files/{filename}"


def get_worker_bucket_key(session_id, output_dir, filename):
    return f"session-{session_id}/{output_dir}/{filename}"


def get_site(user, site_id):
    if user.is_anonymous:
        return None

    sites = Site.objects.filter(pk=site_id)
    sites = sites.filter(
        Q(hosts__user=user, hosts__rights=Membership.EDIT) | Q(created_by=user)
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
            get_bucket_key(site, request.user, filename), client_action
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
                get_worker_bucket_key(session_id, output_dir, filename), client_action
            )

            return Response({"url": url})

        except Exception as e:
            log.exception("Cant create presigned url for worker")

        return Response(status=status.HTTP_403_FORBIDDEN)


class FileUploaded(APIView):
    def post(self, request, format=None):
        site_id = request.data.get("site_id")
        filename = request.data.get("filename")
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
        filename = request.data.get("filename")

        site = get_site(request.user, site_id)
        if site is None:
            return Response(status=status.HTTP_403_FORBIDDEN)

        bucket_key = get_bucket_key(site, request.user, filename)

        s3 = S3()
        s3.delete_file(bucket_key)

        UploadedFile.objects.filter(filepath=bucket_key, hosted_on=site).delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class WorkerAddFile(APIView):
    def post(self, request, format=None):
        worker_id = request.data.get("worker_id")
        session_id = request.data.get("session_id")
        notebook_id = request.data.get("notebook_id")

        filename = request.data.get("filename")
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
            print("worker uploaded files")
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
