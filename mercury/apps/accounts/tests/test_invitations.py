# Please run tests with below command
# python manage.py test apps.accounts

from datetime import datetime

from allauth.account.admin import EmailAddress
from django.contrib.auth.models import User
from django.core import mail
from django.utils.timezone import make_aware
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.accounts.models import Invitation, Membership, Site
from apps.accounts.tasks import task_send_invitation, task_send_new_member
from apps.notebooks.models import Notebook
from apps.workers.models import Worker


class InvitationsTestCase(APITestCase):
    register_url = "/api/v1/auth/register/"
    login_url = "/api/v1/auth/login/"
    invite_url = "/api/v1/{}/invite"
    list_invitations_url = "/api/v1/{}/list-invitations"
    delete_invitation_url = "/api/v1/{}/delete-invitation/{}"

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

    def test_send_invitation(self):
        # login
        response = self.client.post(self.login_url, self.user1_params)
        token = response.json()["key"]
        headers = {"HTTP_AUTHORIZATION": "Token " + token}

        new_data = {"email": "some@example.com", "rights": "EDIT"}

        response = self.client.post(
            self.invite_url.format(self.site.id), new_data, **headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(Invitation.objects.all()), 1)

        task_send_invitation({"invitation_id": 1})

        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue("invites" in mail.outbox[0].body)
        self.assertTrue("edit" in mail.outbox[0].body)
        self.assertTrue(new_data["email"] in mail.outbox[0].to)

        new_data = {
            "email": new_data["email"],
            "password1": "verysecret",
            "password2": "verysecret",
        }
        response = self.client.post(self.register_url, new_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_invite_already_registered_user(self):
        new_email = "some@example.com"
        new_data = {
            "email": new_email,
            "password1": "verysecret",
            "password2": "verysecret",
        }
        response = self.client.post(self.register_url, new_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # login
        response = self.client.post(self.login_url, self.user1_params)
        token = response.json()["key"]
        # create invitation
        headers = {"HTTP_AUTHORIZATION": "Token " + token}
        new_data = {"email": new_email, "rights": "EDIT"}
        response = self.client.post(
            self.invite_url.format(self.site.id), new_data, **headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(Invitation.objects.all()), 0)

        self.assertEqual(len(Membership.objects.all()), 1)

        task_send_new_member({"membership_id": 1})

        # first email is from registration
        # second email is invitations
        self.assertEqual(len(mail.outbox), 2)
        self.assertTrue("invites" in mail.outbox[1].body)
        self.assertTrue("edit" in mail.outbox[1].body)
        self.assertTrue(new_email in mail.outbox[1].to)

    def test_list_invitations(self):
        # login
        response = self.client.post(self.login_url, self.user1_params)
        token = response.json()["key"]
        # create invitation
        new_email = "some@example.com"
        headers = {"HTTP_AUTHORIZATION": "Token " + token}
        new_data = {"email": new_email, "rights": "VIEW"}
        response = self.client.post(
            self.invite_url.format(self.site.id), new_data, **headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(Invitation.objects.all()), 1)

        response = self.client.get(
            self.list_invitations_url.format(self.site.id), **headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["invited"], new_email)

    def test_delete_invitation(self):
        # login
        response = self.client.post(self.login_url, self.user1_params)
        token = response.json()["key"]
        # create invitation
        new_email = "some@example.com"
        headers = {"HTTP_AUTHORIZATION": "Token " + token}
        new_data = {"email": new_email, "rights": "VIEW"}
        response = self.client.post(
            self.invite_url.format(self.site.id), new_data, **headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(Invitation.objects.all()), 1)

        response = self.client.delete(
            self.delete_invitation_url.format(self.site.id, 1), **headers
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.status_code, 204)
