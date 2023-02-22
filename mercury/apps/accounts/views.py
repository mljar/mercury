import json
from datetime import datetime, timedelta

from django.db import transaction
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Site, Membership
from apps.accounts.serializers import SiteSerializer


def max_number_of_sites(user):
    return 10


class SiteViewSet(viewsets.ModelViewSet):
    serializer_class = SiteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # list all user sites
        my_sites = Site.objects.filter(created_by=self.request.user)

        # list all sites where user belons
        memberships = Membership.objects.filter(user=self.request.user).values_list(
            "hosted_on", flat=True
        )
        belong_sites = Site.objects.filter(pk__in=memberships)

        # return union
        return my_sites.union(belong_sites)
        