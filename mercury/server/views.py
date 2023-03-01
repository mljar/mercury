import os

from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Site, Membership


class VersionInfo(APIView):
    def get(self, request, format=None):
        return Response({"isPro": True})


# it will be used as really simple cache
welcome_msg = None


class WelcomeMessage(APIView):
    def get(self, request, site_id, format=None):
        global welcome_msg
        welcome_file = os.environ.get("WELCOME")
        if welcome_file is not None:
            if welcome_msg is None:
                if os.path.exists(welcome_file):
                    with open(welcome_file, encoding="utf-8", errors="ignore") as fin:
                        welcome_msg = fin.read()
                else:
                    return Response({"msg": ""})
            if welcome_msg is not None:
                # check access rights ...
                user = request.user

                site = Site.objects.get(pk=site_id)
                if site.share == Site.PRIVATE:
                    if user.is_anonymous:
                        return Response({"msg": ""})
                    else:
                        # logged user needs to be owner or have member rights
                        owner = site.created_by == user
                        member = Membership.objects.filter(user=user, host=site)
                        if not owner and not member:
                            return Response({"msg": ""})

                return Response({"msg": welcome_msg})
        return Response({"msg": ""})
