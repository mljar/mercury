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

from apps.storage.views.dashboardfiles import get_site

log = logging.getLogger(__name__)


def pro_upload_allowed(user, site_id, filesize):
    if not is_cloud_version():
        return True

    if int(filesize) / 1024 / 1024 > 5:  # 5 MB file limit
        return False

    plan = get_plan(user)

    if plan == PLAN_STARTER:
        return False

    return True


class StyleUrlPut(APIView):
    def get(self, request, site_id, filename, filesize, format=None):
        try:
            if not is_cloud_version():
                return Response({})
            site = get_site(request.user, site_id)
            if site is None:
                return Response(status=status.HTTP_403_FORBIDDEN)

            upload_allowed = pro_upload_allowed(site.created_by, site_id, filesize)
            if not upload_allowed:
                return Response(status=status.HTTP_403_FORBIDDEN)

            s3 = S3()
            url = s3.get_presigned_url(
                get_bucket_key(site, site.created_by, filename.replace(" ", "-")),
                "put_object",
            )
            return Response({"url": url})
        except Exception as e:
            log.exception("Cant create presigned PUT url for style files")

        return Response(status=status.HTTP_403_FORBIDDEN)


class StyleUrlGet(APIView):
    def get(
        self,
        request,
        site_id,
        filename,
        format=None,
    ):
        try:
            if not is_cloud_version():
                return Response({})

            sites = Site.objects.filter(pk=site_id)
            if not sites:
                return Response(status=status.HTTP_404_NOT_FOUND)

            if sites[0].share == Site.PRIVATE:
                if request.user.is_anonymous:
                    return Response(status=status.HTTP_403_FORBIDDEN)

                sites = sites.filter(
                    # any Membership (VIEW or EDIT) or owner
                    Q(
                        pk__in=Membership.objects.filter(user=self.request.user).values(
                            "host__id"
                        )
                    )
                    | Q(created_by=self.request.user)
                )

                if not sites:
                    return Response(status=status.HTTP_403_FORBIDDEN)

            site = sites[0]

            s3 = S3()
            url = s3.get_presigned_url(
                get_bucket_key(site, site.created_by, filename.replace(" ", "-")),
                "get_object",
            )

            return Response({"url": url})

        except Exception as e:
            log.exception("Cant GET presigned url for style files")

        return Response(status=status.HTTP_403_FORBIDDEN)
