import json
import uuid
from datetime import datetime, timedelta

from django.db import transaction
from django.db.models import Q
from django.template.defaultfilters import slugify
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Membership, Site
from apps.accounts.serializers import MembershipSerializer, SiteSerializer


def some_random_slug():
    h = uuid.uuid4().hex.replace("-", "")
    return h[:8]


def get_slug(slug, title):
    new_slug = slugify(slug)
    if new_slug == "":
        new_slug = slugify(title)
    if new_slug == "":
        new_slug = some_random_slug()
    return new_slug


class SiteViewSet(viewsets.ModelViewSet):
    serializer_class = SiteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Site.objects.filter(
            Q(hosts__user=self.request.user, hosts__rights=Membership.EDIT)
            | Q(created_by=self.request.user)
        )

    def create(self, request, *args, **kwargs):
        # here we can check number of allowed sites
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def perform_create(self, serializer):
        try:
            # create a database instance
            with transaction.atomic():
                instance = serializer.save(created_by=self.request.user)

                instance.slug = get_slug(instance.slug, instance.title)

                instance.save()
        except Exception as e:
            raise APIException(str(e))

    def perform_update(self, serializer):
        updated_instance = serializer.save()
        # lets check slug if we update it
        new_slug = self.request.data.get("slug")
        if new_slug is not None:
            updated_instance.slug = get_slug(new_slug, updated_instance.title)
            updated_instance.save()

    def destroy(self, request, *args, **kwargs):
        """Only owner can delete object"""
        try:
            instance = self.get_object()
            if instance.created_by == self.request.user:
                self.perform_destroy(instance)
            else:
                return Response(status=status.HTTP_404_NOT_FOUND)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MembershipViewSet(viewsets.ModelViewSet):
    serializer_class = MembershipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Membership.objects.filter(
            host__id=self.kwargs["site_id"]
        )
        