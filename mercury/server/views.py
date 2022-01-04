from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response


class VersionInfo(APIView):
    def get(self, request, format=None):

        return Response({"isPro": False})
