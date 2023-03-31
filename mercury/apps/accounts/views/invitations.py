import json
import os
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
from apps.accounts.serializers import InvitationSerializer
from apps.accounts.tasks import (
    task_init_site,
    task_send_invitation,
    task_send_new_member,
)
from apps.accounts.views.permissions import HasEditRights


class InviteView(APIView):
    permission_classes = [permissions.IsAuthenticated, HasEditRights]

    def post(self, request, site_id, format=None):
        try:
            # create a database instance
            with transaction.atomic():
                address_email = request.data.get("email")

                if address_email == request.user.email:
                    # dont need to invite user herself
                    return Response(status=status.HTTP_200_OK)

                rights = request.data.get("rights", "VIEW")
                if rights not in ["VIEW", "EDIT"]:
                    rights = "VIEW"

                site = Site.objects.get(pk=site_id)

                # check for users
                already_user = User.objects.filter(email=address_email)

                if already_user:
                    # check if membership exists
                    if Membership.objects.filter(
                        user=already_user[0], host=site, rights=rights
                    ):
                        return Response(status=status.HTTP_200_OK)
                    else:
                        # need to create a new one
                        membership = Membership.objects.create(
                            user=already_user[0],
                            host=site,
                            rights=rights,
                            created_by=request.user,
                        )
                        job_params = {"membership_id": membership.id}
                        transaction.on_commit(
                            lambda: task_send_new_member.delay(job_params)
                        )

                else:
                    # check if invitation already exists
                    if Invitation.objects.filter(
                        invited=address_email, rights=rights, hosted_on=site
                    ):
                        return Response(status=status.HTTP_200_OK)
                    else:
                        # lets create a new invitation
                        invitation = Invitation.objects.create(
                            invited=address_email,
                            created_by=request.user,
                            rights=rights,
                            hosted_on=site,
                        )

                        job_params = {"invitation_id": invitation.id}
                        transaction.on_commit(
                            lambda: task_send_invitation.delay(job_params)
                        )

                return Response(status=status.HTTP_200_OK)
        except Exception as e:
            raise APIException(str(e))


class ListInvitations(APIView):
    permission_classes = [permissions.IsAuthenticated, HasEditRights]

    def get(self, request, site_id, format=None):
        try:
            invitations = Invitation.objects.filter(hosted_on__id=site_id)
            return Response(
                InvitationSerializer(invitations, many=True).data,
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            print(str(e))
            raise APIException(str(e))


class DeleteInvitation(APIView):
    permission_classes = [permissions.IsAuthenticated, HasEditRights]

    def delete(self, request, site_id, invitation_id, format=None):
        try:
            invitation = Invitation.objects.get(pk=invitation_id, hosted_on__id=site_id)
            invitation.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            raise APIException(str(e))
