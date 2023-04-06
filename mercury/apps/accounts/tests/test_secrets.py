# Please run tests with below command
# python manage.py test apps.accounts.tests.test_secrets

from datetime import datetime

from allauth.account.admin import EmailAddress
from django.contrib.auth.models import User
from django.utils.timezone import make_aware
from rest_framework.test import APITestCase

from apps.accounts.models import Membership, Secret, Site
from apps.notebooks.models import Notebook
from apps.workers.models import Worker


class SecretsTestCase(APITestCase):
    register_url = "/api/v1/auth/register/"
    login_url = "/api/v1/auth/login/"
    add_secret_url = "/api/v1/{}/add-secret"
    list_secrets_url = "/api/v1/{}/list-secrets"
    delete_secret_url = "/api/v1/{}/delete-secret/{}"

    def setUp(self):
        self.user1_params = {
            "username": "user1",  # it is optional to pass username
            "email": "piotr@example.com",
            "password": "verysecret",
        }
        self.user = User.objects.create_user(
            username=self.user1_params["username"],
            email=self.user1_params["email"],
            password=self.user1_params["password"],
        )
        EmailAddress.objects.create(
            user=self.user, email=self.user.email, verified=True, primary=True
        )
        self.site = Site.objects.create(
            title="First site", slug="first-site", created_by=self.user
        )

    def test_add_secret(self):
        # login
        response = self.client.post(self.login_url, self.user1_params)
        token = response.json()["key"]
        headers = {"HTTP_AUTHORIZATION": "Token " + token}
        new_data = {"name": "MY_SECRET", "secret": "super-secret"}
        response = self.client.post(
            self.add_secret_url.format(self.site.id), new_data, **headers
        )
        secrets = Secret.objects.all()

        self.assertEqual(len(secrets), 1)
        self.assertEqual(secrets[0].name, new_data["name"])
        self.assertNotEqual(secrets[0].token, new_data["secret"])

        response = self.client.get(
            self.list_secrets_url.format(self.site.id), **headers
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], new_data["name"])

    def test_list_worker_secrets(self):
        # login
        response = self.client.post(self.login_url, self.user1_params)
        token = response.json()["key"]
        headers = {"HTTP_AUTHORIZATION": "Token " + token}
        new_data = {"name": "MY_SECRET", "secret": "super-secret"}
        response = self.client.post(
            self.add_secret_url.format(self.site.id), new_data, **headers
        )

        nb = Notebook.objects.create(
            title="some",
            slug="some",
            path="some",
            created_by=self.user,
            hosted_on=self.site,
            file_updated_at=make_aware(datetime.now()),
        )
        session_id = "some-session"
        worker = Worker.objects.create(
            session_id=session_id, machine_id="some-machine", notebook=nb
        )

        # get worker secrets
        url = f"/api/v1/worker/{session_id}/{worker.id}/{nb.id}/worker-secrets"
        response = self.client.get(url)
        self.assertEqual(response.json()[0].get("name"), new_data["name"])
        self.assertEqual(response.json()[0].get("secret"), new_data["secret"])

    def test_delete_secret(self):
        # login
        response = self.client.post(self.login_url, self.user1_params)
        token = response.json()["key"]
        headers = {"HTTP_AUTHORIZATION": "Token " + token}
        new_data = {"name": "MY_SECRET", "secret": "super-secret"}
        response = self.client.post(
            self.add_secret_url.format(self.site.id), new_data, **headers
        )
        secrets = Secret.objects.all()
        self.assertEqual(len(secrets), 1)

        response = self.client.delete(
            self.delete_secret_url.format(self.site.id, 1), **headers
        )
        self.assertEqual(response.status_code, 204)
        secrets = Secret.objects.all()
        self.assertEqual(len(secrets), 0)

    def test_list_secrets_by_user(self):
        # login
        response = self.client.post(self.login_url, self.user1_params)
        token = response.json()["key"]
        headers = {"HTTP_AUTHORIZATION": "Token " + token}
        new_data = {"name": "MY_SECRET", "secret": "super-secret"}
        response = self.client.post(
            self.add_secret_url.format(self.site.id), new_data, **headers
        )

        # get worker secrets
        url = f"/api/v1/{self.site.id}/list-secrets"
        response = self.client.get(url, **headers)
        self.assertTrue(len(response.json()), 1)

        user2_params = {
            "username": "user2",  # it is optional to pass username
            "email": "piotr2@example.com",
            "password": "verysecret2",
        }
        user2 = User.objects.create_user(
            username=user2_params["username"],
            email=user2_params["email"],
            password=user2_params["password"],
        )
        EmailAddress.objects.create(
            user=user2, email=user2.email, verified=True, primary=True
        )

        response = self.client.post(self.login_url, user2_params)
        token = response.json()["key"]
        headers = {"HTTP_AUTHORIZATION": "Token " + token}

        url = f"/api/v1/{self.site.id}/list-secrets"
        response = self.client.get(url, **headers)
        self.assertTrue(len(response.json()), 0)

        # invite
        m = Membership.objects.create(
            user=user2, host=self.site, rights=Membership.VIEW, created_by=self.user
        )

        url = f"/api/v1/{self.site.id}/list-secrets"
        response = self.client.get(url, **headers)
        self.assertTrue(len(response.json()), 0)

        m.rights = Membership.EDIT
        m.save()

        url = f"/api/v1/{self.site.id}/list-secrets"
        response = self.client.get(url, **headers)
        self.assertTrue(len(response.json()), 1)
