from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.db.models import Q

from apps.accounts.models import Membership, Site
from apps.storage.s3utils import S3
from apps.storage.models import UploadedFile


def get_bucket_key(user, site, filename):
    return f"user-{user.id}/site-{site.id}/{filename}"


class ListFiles(APIView):
    def get(self, request, site_id, format=None):
        return JsonResponse([], safe=False)


class GetPutPresignedUrl(APIView):
    def get(self, request, site_id, filename, format=None):
        if request.user.is_anonymous:
            return Response(status=status.HTTP_403_FORBIDDEN)

        sites = Site.objects.filter(pk=site_id)
        sites = sites.filter(
            Q(hosts__user=self.request.user, hosts__rights=Membership.EDIT)
            | Q(created_by=self.request.user)
        )
        if not sites:
            return Response(status=status.HTTP_403_FORBIDDEN)

        s3 = S3()
        url = s3.get_presigned_url(
            get_bucket_key(request.user, sites[0], filename), "put_object"
        )
        return Response({"url": "url"}, safe=False)


class FileUploaded(APIView):
    def post(self, request, site_id, filename, format=None):
        if request.use.is_anonymous:
            return Response(status=status.HTTP_403_FORBIDDEN)

        site_id = request.data.get("site_id")
        filename = request.data.get("site_id")

        sites = Site.objects.filter(pk=site_id)
        sites = sites.filter(
            Q(hosts__user=self.request.user, hosts__rights=Membership.EDIT)
            | Q(created_by=self.request.user)
        )
        if not sites:
            return Response(status=status.HTTP_403_FORBIDDEN)

        bucket_key = get_bucket_key(request.user, sites[0], filename)

        UploadedFile.objects.create(
            filename=filename,
            filepath=bucket_key,
            filetype="aha",
            filesize=1,
            hosted_on=sites[0],
            created_by=request.user,
        )

        return Response(status=status.HTTP_200_OK)
