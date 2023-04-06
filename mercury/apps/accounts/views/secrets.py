import os

from cryptography.fernet import Fernet
from rest_framework import permissions, status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Secret, Site
from apps.accounts.views.permissions import HasEditRights
from apps.notebooks.models import Notebook
from apps.workers.models import Worker
from apps.accounts.serializers import SecretSerializer


class AddSecret(APIView):
    permission_classes = [permissions.IsAuthenticated, HasEditRights]

    def post(self, request, site_id, format=None):
        site = Site.objects.get(pk=site_id)

        name = request.data.get("name")
        secret = request.data.get("secret")

        # print(Fernet.generate_key())

        f = Fernet(
            os.environ.get(
                "FERNET_KEY", "ZpojyumLN_yNMwhZH21pXmHA3dgB74Tlcx9lb3wAtmE="
            ).encode()
        )

        Secret.objects.create(
            name=name,
            token=f.encrypt(secret.encode()).decode(),
            created_by=request.user,
            hosted_on=site,
        )

        return Response(status=status.HTTP_201_CREATED)


class ListSecrets(APIView):
    permission_classes = [permissions.IsAuthenticated, HasEditRights]

    def get(self, request, site_id, format=None):
        secrets = Secret.objects.filter(hosted_on__id=site_id)

        return Response(
            SecretSerializer(secrets, many=True).data, status=status.HTTP_200_OK
        )


class WorkerListSecrets(APIView):
    def get(self, request, session_id, worker_id, notebook_id, format=None):
        try:
            w = Worker.objects.get(
                pk=worker_id, session_id=session_id, notebook__id=notebook_id
            )
            nb = Notebook.objects.get(pk=notebook_id)
            secrets = Secret.objects.filter(hosted_on=nb.hosted_on)
            data = []

            f = Fernet(
                os.environ.get(
                    "FERNET_KEY", "ZpojyumLN_yNMwhZH21pXmHA3dgB74Tlcx9lb3wAtmE="
                ).encode()
            )

            for secret in secrets:
                data += [
                    {
                        "name": secret.name,
                        "secret": f.decrypt(secret.token.encode()).decode(),
                    }
                ]

            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(status=status.HTTP_404_NOT_FOUND)


class DeleteSecret(APIView):
    permission_classes = [permissions.IsAuthenticated, HasEditRights]

    def delete(self, request, site_id, secret_id, format=None):
        try:
            secret = Secret.objects.get(pk=secret_id, hosted_on__id=site_id)
            secret.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            raise APIException(str(e))
