from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import permissions, viewsets
from rest_framework.exceptions import APIException

from apps.accounts.models import Membership, Site
from apps.accounts.serializers import MembershipSerializer

from apps.accounts.views.permissions import HasEditRights

import json
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.serializers import ValidationError

from apps.accounts.serializers import UserSerializer


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


class DeleteAccount(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):
        user = request.user

        info = json.loads(user.profile.info)
        plan = info.get("plan", "starter")
        if plan != "starter":
            return Response(
                data={"msg": "Please cancel subscription"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # remove other stuff ...
        print("TODO: remove all files ...")

        user.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
