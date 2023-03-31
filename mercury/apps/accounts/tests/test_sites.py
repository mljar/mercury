# Please run tests with below command
# python manage.py test apps.accounts
import os
from datetime import datetime

from allauth.account.admin import EmailAddress
from django.contrib.auth.models import User
from django.core import mail
from django.utils.timezone import make_aware
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.accounts.models import Membership, Secret, Site
from apps.notebooks.models import Notebook
from apps.workers.models import Worker


class SitesTestCase(APITestCase):
    register_url = "/api/v1/auth/register/"
    verify_email_url = "/api/v1/auth/register/verify-email/"
    login_url = "/api/v1/auth/login/"
    user_details_url = "/api/v1/auth/user/"
    logout_url = "/api/v1/auth/logout/"
    delete_account_url = "/api/v1/auth/delete-account/"
    change_password_url = "/api/v1/auth/password/change/"
    reset_password_url = "/api/v1/auth/password/reset/"
    reset_password_confirm_url = "/api/v1/auth/password/reset/confirm/"

    sites_url = "/api/v1/sites/"
    members_url = "/api/v1/{}/members/"  # need to set site_id
    invite_url = "/api/v1/{}/invite/"

    def setUp(self):
        #
        # first user
        #
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
        #
        # second user
        #
        self.user2_params = {
            "username": "user2",  # it is optional to pass username
            "email": "piotr2@example.com",
            "password": "verysecret2",
        }
        self.user2 = User.objects.create_user(
            username=self.user2_params["username"],
            email=self.user2_params["email"],
            password=self.user2_params["password"],
        )
        EmailAddress.objects.create(
            user=self.user2, email=self.user2.email, verified=True, primary=True
        )

    def test_list_sites(self):
        site = Site.objects.create(
            title="First site", slug="first-site", created_by=self.user
        )
        # login as first user to get token
        response = self.client.post(self.login_url, self.user1_params)
        token = response.json()["key"]
        headers = {"HTTP_AUTHORIZATION": "Token " + token}
        response = self.client.get(self.sites_url, **headers)
        self.assertEqual(len(response.json()), 1)

        # login as second user
        response = self.client.post(self.login_url, self.user2_params)
        token = response.json()["key"]
        headers = {"HTTP_AUTHORIZATION": "Token " + token}
        response = self.client.get(self.sites_url, **headers)
        self.assertEqual(len(response.json()), 0)
        # add rights to edit
        Membership.objects.create(
            user=self.user2, host=site, rights=Membership.EDIT, created_by=self.user
        )
        response = self.client.get(self.sites_url, **headers)
        self.assertEqual(len(response.json()), 1)

    def test_get_site(self):
        site = Site.objects.create(
            title="First site", slug="first-site", created_by=self.user
        )
        # login to get token
        response = self.client.post(self.login_url, self.user1_params)
        token = response.json()["key"]
        headers = {"HTTP_AUTHORIZATION": "Token " + token}

        response = self.client.get(f"{self.sites_url}1/", **headers)
        for key in ["title", "slug", "share", "created_by", "created_at"]:
            self.assertTrue(key in response.json())

    def test_create_site(self):
        # login to get token
        response = self.client.post(self.login_url, self.user1_params)
        token = response.json()["key"]
        headers = {"HTTP_AUTHORIZATION": "Token " + token}

        # no sites in database
        response = self.client.get(self.sites_url, **headers)
        self.assertEqual(len(response.json()), 0)
        # create site
        new_data = {"title": "New site", "slug": "Some slug", "share": Site.PRIVATE}
        response = self.client.post(self.sites_url, new_data, **headers)
        self.assertEqual(response.status_code, 201)
        for key in ["title", "slug", "share", "created_by", "created_at"]:
            self.assertTrue(key in response.json())

    def test_destroy_site(self):
        # create site for first user
        site = Site.objects.create(
            title="First site", slug="first-site", created_by=self.user
        )
        # login as second user to get token
        response = self.client.post(self.login_url, self.user2_params)
        token = response.json()["key"]
        headers = {"HTTP_AUTHORIZATION": "Token " + token}

        # second user cant delete
        response = self.client.delete(f"{self.sites_url}1/", **headers)
        self.assertEqual(response.status_code, 404)

        # login as first user to get token
        response = self.client.post(self.login_url, self.user1_params)
        token = response.json()["key"]
        headers = {"HTTP_AUTHORIZATION": "Token " + token}

        response = self.client.get(self.sites_url, **headers)
        self.assertEqual(len(response.json()), 1)

        # first user delete site because only owner can delete
        response = self.client.delete(f"{self.sites_url}1/", **headers)
        self.assertEqual(response.status_code, 204)

        response = self.client.get(self.sites_url, **headers)
        self.assertEqual(len(response.json()), 0)

    def test_update_site(self):
        # create site for first user
        site = Site.objects.create(
            title="First site", slug="first-site", created_by=self.user
        )

        # login as second user to get token
        response = self.client.post(self.login_url, self.user2_params)
        token = response.json()["key"]
        headers = {"HTTP_AUTHORIZATION": "Token " + token}

        new_data = {"title": "New title", "slug": "new-slug", "share": Site.PRIVATE}
        # try to edit without edit rights
        response = self.client.put(f"{self.sites_url}1/", new_data, **headers)
        self.assertEqual(response.status_code, 404)

        # give edit access to second user
        Membership.objects.create(
            user=self.user2, host=site, rights=Membership.EDIT, created_by=self.user
        )
        # second user can edit
        response = self.client.put(f"{self.sites_url}1/", new_data, **headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["title"], new_data["title"])
        self.assertEqual(data["slug"], new_data["slug"])
        self.assertEqual(data["share"], new_data["share"])

    def test_update_site_invalid_slug(self):
        # create site for first user
        site = Site.objects.create(
            title="First site", slug="first-site", created_by=self.user
        )

        # login as second user to get token
        response = self.client.post(self.login_url, self.user2_params)
        token = response.json()["key"]
        headers = {"HTTP_AUTHORIZATION": "Token " + token}

        new_data = {"title": "New title", "slug": "mljar", "share": Site.PRIVATE}
        # try to edit without edit rights
        response = self.client.put(f"{self.sites_url}1/", new_data, **headers)
        self.assertEqual(response.status_code, 404)

        # give edit access to second user
        Membership.objects.create(
            user=self.user2, host=site, rights=Membership.EDIT, created_by=self.user
        )
        # second user can edit
        response = self.client.put(f"{self.sites_url}1/", new_data, **headers)
        self.assertEqual(response.status_code, 400)
        self.assertTrue("You cant" in response.json()[0])

        # second user can edit
        response = self.client.patch(
            f"{self.sites_url}1/", {"slug": "mljar"}, **headers
        )
        self.assertEqual(response.status_code, 400)
        self.assertTrue("You cant" in response.json()[0])

        # second user can edit
        response = self.client.patch(
            f"{self.sites_url}1/", {"title": "new title"}, **headers
        )
        self.assertEqual(response.status_code, 200)

    def test_limit_sites(self):
        # login to get token
        response = self.client.post(self.login_url, self.user1_params)
        token = response.json()["key"]
        headers = {"HTTP_AUTHORIZATION": "Token " + token}

        # no sites in database
        response = self.client.get(self.sites_url, **headers)
        self.assertEqual(len(response.json()), 0)
        # create site
        new_data = {"title": "New site", "slug": "Some slug", "share": Site.PRIVATE}
        response = self.client.post(self.sites_url, new_data, **headers)
        self.assertEqual(response.status_code, 201)

        os.environ["MERCURY_CLOUD"] = "1"
        # create site, but limit should be reached
        new_data = {"title": "New site", "slug": "Some slug 2", "share": Site.PRIVATE}
        response = self.client.post(self.sites_url, new_data, **headers)
        self.assertEqual(response.status_code, 403)

        os.environ["MERCURY_CLOUD"] = "0"
        # create site, now it should work
        new_data = {
            "title": "New site",
            "slug": "Some slug 2 asd",
            "share": Site.PRIVATE,
        }
        response = self.client.post(self.sites_url, new_data, **headers)
        print(response.content)
        self.assertEqual(response.status_code, 201)

        # create site with the same slug
        new_data = {"title": "New site", "slug": "Some slug", "share": Site.PRIVATE}
        response = self.client.post(self.sites_url, new_data, **headers)
        self.assertEqual(response.status_code, 403)

        # create site with the forbidden slug
        new_data = {"title": "New site", "slug": "mercury", "share": Site.PRIVATE}
        response = self.client.post(self.sites_url, new_data, **headers)
        self.assertEqual(response.status_code, 403)

    def test_list_sites_with_members(self):
        # create site for first user
        site = Site.objects.create(
            title="First site", slug="first-site", created_by=self.user
        )
        # add memberships
        Membership.objects.create(
            user=self.user, host=site, rights=Membership.EDIT, created_by=self.user
        )
        Membership.objects.create(
            user=self.user, host=site, rights=Membership.EDIT, created_by=self.user
        )
        Membership.objects.create(
            user=self.user, host=site, rights=Membership.EDIT, created_by=self.user
        )

        # login as second user to get token
        response = self.client.post(self.login_url, self.user1_params)
        token = response.json()["key"]
        headers = {"HTTP_AUTHORIZATION": "Token " + token}

        # there should be only 1 site - shouldnt depend on members count
        response = self.client.get(f"{self.sites_url}", **headers)
        self.assertTrue(len(response.json()), 1)
