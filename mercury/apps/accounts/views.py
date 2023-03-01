import json
import uuid
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.template.defaultfilters import slugify
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Invitation, Membership, Site
from apps.accounts.serializers import MembershipSerializer, SiteSerializer
from apps.accounts.tasks import task_send_invitation


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


class HasEditRights(permissions.BasePermission):
    def has_permission(self, request, view):
        site_id = view.kwargs.get("site_id")
        if site_id is None:  # just in case
            return False
        return (
            Membership.objects.filter(
                host__id=site_id, user=request.user, rights=Membership.EDIT
            )
            or Site.objects.get(pk=site_id).created_by == request.user
        )

    def has_object_permission(self, request, view, obj):
        return (
            Membership.objects.filter(
                host=obj.host, user=request.user, rights=Membership.EDIT
            )
            or obj.host.created_by == request.user
        )


class MembershipViewSet(viewsets.ModelViewSet):
    serializer_class = MembershipSerializer
    permission_classes = [permissions.IsAuthenticated, HasEditRights]

    def get_queryset(self):
        return Membership.objects.filter(host__id=self.kwargs["site_id"])

    def perform_create(self, serializer):
        try:
            # create a database instance
            with transaction.atomic():
                site = Site.objects.get(pk=self.kwargs.get("site_id"))
                user = User.objects.get(pk=self.request.data.get("user_id"))
                instance = serializer.save(
                    host=site, user=user, created_by=self.request.user
                )
                instance.save()
        except Exception as e:
            raise APIException(str(e))


class InviteView(APIView):
    permission_classes = [permissions.IsAuthenticated, HasEditRights]

    def post(self, request, site_id, format=None):
        try:
            # create a database instance
            with transaction.atomic():
                address_email = request.data.get("email")
                token = uuid.uuid4().hex.replace("-", "")[:8]

                invitation = Invitation.objects.create(
                    token=token, invited=address_email, created_by=request.user
                )

                job_params = {"db_id": invitation.id}
                transaction.on_commit(lambda: task_send_invitation.delay(job_params))

                return Response(status=status.HTTP_200_OK)
        except Exception as e:
            raise APIException(str(e))


class GetSiteView(APIView):
    def get(self, request, site_slug, format=None):
        
        sites = Site.objects.filter(slug=site_slug)
        if not sites:
            return Response(status=status.HTTP_404_NOT_FOUND)

        share = Site.PUBLIC if request.user.is_anonymous else Site.PRIVATE
        sites = sites.filter(share=share)
        
        if not request.user.is_anonymous:
            sites = sites.filter(
                Q(hosts__user=self.request.user, hosts__rights=Membership.EDIT)
                | Q(hosts__user=self.request.user, hosts__rights=Membership.EDIT)
                | Q(created_by=self.request.user)
            )

        if not sites:
            return Response(status=status.HTTP_403_FORBIDDEN)

        return Response(SiteSerializer(sites[0]).data)
