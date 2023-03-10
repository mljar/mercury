from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.db.models import Q

from apps.accounts.models import Membership, Site
from apps.storage.s3utils import S3
from apps.storage.models import UploadedFile
from apps.storage.serializers import UploadedFileSerializer


def get_bucket_key(site, user, filename):
    return f"site-{site.id}/user-{user.id}/{filename}"


def get_site_bucket_key(site, filename):
    return f"site-{site.id}/files/{filename}"


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

        client_action = "put_object" if action == "put" else "get_object"

        s3 = S3()
        url = s3.get_presigned_url(
            get_bucket_key(site, request.user, filename), client_action
        )
        return Response({"url": url})


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
