from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.accounts.models import ApiKey


class GetApiKey(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):
        api_key, _ = ApiKey.objects.get_or_create(user=request.user)
        return Response({"apiKey": api_key.key}, status=status.HTTP_200_OK)


class RegenerateApiKey(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):
        ApiKey.objects.filter(user=request.user).update(key=ApiKey.generate_key())
        api_key = ApiKey.objects.get(user=request.user)
        return Response({"apiKey": api_key.key}, status=status.HTTP_200_OK)
